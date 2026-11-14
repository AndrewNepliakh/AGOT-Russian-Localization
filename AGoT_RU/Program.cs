using System.Text;
using System.Text.Json;
using System.Reflection;
using System.Diagnostics;
using System.IO.Compression;
using System.Security.Cryptography;

internal static class Program
{
    const string Data = "AGameOfThronesTheBoardGame_Data/";
    const string BackupName = "RussianLocalization_Backup";
    const string Marker = "AGoT_RU_manifest.json";

    static int Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.WriteLine("AGoT RU — русификатор A Game of Thrones: The Board Game");
        try { return Run(args); }
        catch (Exception ex) { Console.Error.WriteLine("ОШИБКА: " + ex.Message); return 1; }
        finally { if (!Console.IsInputRedirected) { Console.WriteLine("Нажмите Enter для выхода..."); Console.ReadLine(); } }
    }

    static int Run(string[] args)
    {
        if (args.Length > 1 || (args.Length == 1 && args[0] != "--restore"))
            throw new Exception("Использование: AGoT_RU.exe [--restore]");
        bool restore = args.Length == 1;
        string root = AppContext.BaseDirectory;
        if (!File.Exists(Path.Combine(root, "AGameOfThronesTheBoardGame.exe")))
            throw new Exception("Поместите AGoT_RU.exe рядом с AGameOfThronesTheBoardGame.exe.");
        string backup = Path.Combine(root, BackupName);
        string markerPath = Path.Combine(backup, Marker);
        if (restore)
        {
            if (!File.Exists(markerPath)) throw new Exception("Не найдена резервная копия этой установки.");
            var entries = JsonSerializer.Deserialize<List<Entry>>(File.ReadAllText(markerPath)) ?? throw new Exception("Повреждён манифест резервной копии.");
            Validate(entries);
            foreach (var entry in entries.Where(e => e.Kind == "patch"))
                if (!File.Exists(SafePath(backup, entry.Path))) throw new Exception("Нет резервной копии: " + entry.Path);
          
            foreach (var entry in entries)
            {
                var dest = SafePath(root, entry.Path);
                if (entry.Kind == "patch") File.Copy(SafePath(backup, entry.Path), dest, true);
                else if (File.Exists(dest)) File.Delete(dest);
                Console.WriteLine("Восстановлено: " + entry.Path);
            }
            Directory.Delete(backup, true);
            Console.WriteLine("Оригиналы восстановлены.");
            return 0;
        }
        if (Directory.Exists(backup)) throw new Exception("Резервная копия уже существует. Сначала выполните --restore.");
        string temp = Path.Combine(Path.GetTempPath(), "AGoT_RU_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(temp);
        try
        {
            var payload = Path.Combine(temp, "payload");
            Directory.CreateDirectory(payload);
            ExtractResource("AGoT.Payload.zip", Path.Combine(temp, "payload.zip"));
            ZipFile.ExtractToDirectory(Path.Combine(temp, "payload.zip"), payload);
            string xdelta = Path.Combine(temp, "xdelta3.exe");
            ExtractResource("AGoT.xdelta3.exe", xdelta);
            var manifest = JsonSerializer.Deserialize<List<string>>(File.ReadAllText(Path.Combine(payload, "generated_files.json"))) ?? throw new Exception("Пустой манифест.");
            var entries = manifest.Select(s => s.EndsWith(".xdelta", StringComparison.OrdinalIgnoreCase)
                ? new Entry(s[..^7], "patch") : new Entry(s, "new")).ToList();
            Validate(entries);
            if (entries.Count == 0) throw new Exception("Нет файлов для установки.");
            var staged = Path.Combine(temp, "staged");
            Directory.CreateDirectory(staged);
            foreach (var entry in entries)
            {
                string target = SafePath(root, entry.Path);
                string output = SafePath(staged, entry.Path);
                string source = SafePath(payload, entry.Path + (entry.Kind == "patch" ? ".xdelta" : ""));
                if (!File.Exists(source)) throw new Exception("Отсутствует файл пакета: " + entry.Path);
                if (entry.Kind == "patch" && !File.Exists(target)) throw new Exception("Нет оригинального файла: " + entry.Path);
                if (entry.Kind == "new" && File.Exists(target)) throw new Exception("Файл уже существует: " + entry.Path);
                Directory.CreateDirectory(Path.GetDirectoryName(output)!);
                if (entry.Kind == "patch")
                {
                    Console.WriteLine("Проверка: " + entry.Path);
                    using var p = Process.Start(new ProcessStartInfo(xdelta) {
                        ArgumentList = { "-d", "-f", "-s", target, source, output },
                        UseShellExecute = false, CreateNoWindow = true
                    }) ?? throw new Exception("Не удалось запустить xdelta3");
                    p.WaitForExit();
                    if (p.ExitCode != 0 || !File.Exists(output)) throw new Exception("Патч не подходит к версии игры: " + entry.Path);
                }
                else File.Copy(source, output);
            }
         
            Directory.CreateDirectory(backup);
            foreach (var entry in entries.Where(e => e.Kind == "patch"))
            {
                var dest = SafePath(backup, entry.Path);
                Directory.CreateDirectory(Path.GetDirectoryName(dest)!);
                File.Copy(SafePath(root, entry.Path), dest);
            }
            File.WriteAllText(markerPath, JsonSerializer.Serialize(entries));
            var touched = new List<Entry>();
            try
            {
                foreach (var entry in entries)
                {
                    string dest = SafePath(root, entry.Path);
                    Directory.CreateDirectory(Path.GetDirectoryName(dest)!);
                    touched.Add(entry); // record before copy, for partial-copy rollback
                    File.Copy(SafePath(staged, entry.Path), dest, true);
                    if (!SHA256.HashData(File.ReadAllBytes(dest)).SequenceEqual(SHA256.HashData(File.ReadAllBytes(SafePath(staged, entry.Path)))))
                        throw new IOException("Проверка записанного файла не прошла: " + entry.Path);
                    Console.WriteLine("Установлено: " + entry.Path);
                }
            }
            catch
            {
                foreach (var entry in touched.AsEnumerable().Reverse())
                {
                    try {
                        var dest = SafePath(root, entry.Path);
                        if (entry.Kind == "patch") File.Copy(SafePath(backup, entry.Path), dest, true);
                        else if (File.Exists(dest)) File.Delete(dest);
                    } catch (Exception e) { Console.Error.WriteLine("Не удалось откатить " + entry.Path + ": " + e.Message); }
                }
                // Keep backups for manual recovery if anything fails.
                throw;
            }
            Console.WriteLine("Русификатор установлен. Для удаления запустите AGoT_RU.exe --restore");
            return 0;
        }
        finally { try { Directory.Delete(temp, true); } catch { } }
    }

    static void ExtractResource(string resource, string dest)
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(resource)
            ?? throw new Exception("Отсутствует встроенный ресурс: " + resource);
        using var output = File.Create(dest);
        stream.CopyTo(output);
    }

    static string SafePath(string baseDir, string relative)
    {
        if (!relative.StartsWith(Data, StringComparison.Ordinal) || relative.Contains('\\') || relative.Split('/').Any(p => p is ".." or "" or ".") || Path.IsPathRooted(relative))
            throw new Exception("Недопустимый путь в манифесте: " + relative);
        string baseFull = Path.TrimEndingDirectorySeparator(Path.GetFullPath(baseDir)) + Path.DirectorySeparatorChar;
        string full = Path.GetFullPath(Path.Combine(baseDir, relative.Replace('/', Path.DirectorySeparatorChar)));
        if (!full.StartsWith(baseFull, StringComparison.OrdinalIgnoreCase)) throw new Exception("Путь вне папки игры.");
        return full;
    }

    static void Validate(List<Entry> entries)
    {
        if (entries.Select(e => e.Path).Distinct(StringComparer.OrdinalIgnoreCase).Count() != entries.Count)
            throw new Exception("Дублирующиеся файлы в манифесте.");
        foreach (var e in entries)
        {
            if (e.Kind is not ("patch" or "new")) throw new Exception("Неизвестный тип файла.");
            SafePath(Path.GetTempPath(), e.Path);
        }
    }
    record Entry(string Path, string Kind);
}
