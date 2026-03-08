#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

use tauri::{Manager, WindowEvent};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

#[tauri::command]
fn open_file(path: String) -> Result<String, String> {
    let status = if cfg!(target_os = "macos") {
        Command::new("open").arg(&path).status()
    } else if cfg!(target_os = "windows") {
        Command::new("cmd").args(["/C", "start", "", &path]).status()
    } else {
        Command::new("xdg-open").arg(&path).status()
    }
    .map_err(|err| format!("Failed to execute open command: {err}"))?;

    if status.success() {
        Ok(format!("Opened {path}"))
    } else {
        Err(format!("Open command exited with status: {status}"))
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(|app, shortcut, event| {
                    if event.state() != ShortcutState::Pressed {
                        return;
                    }

                    let ctrl_space = Shortcut::new(Some(Modifiers::CONTROL), Code::Space);
                    if shortcut != &ctrl_space {
                        return;
                    }

                    if let Some(window) = app.get_webview_window("main") {
                        let visible = window.is_visible().unwrap_or(true);
                        if visible {
                            let _ = window.unminimize();
                            let _ = window.show();
                            let _ = window.set_focus();
                        } else {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(),
        )
        .setup(|app| {
            app.global_shortcut()
                .register(Shortcut::new(Some(Modifiers::CONTROL), Code::Space))
                .map_err(|err| -> Box<dyn std::error::Error> { Box::new(err) })?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .invoke_handler(tauri::generate_handler![open_file])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
