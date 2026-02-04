# Aquastilla Softener – Home Assistant Integration

Custom Home Assistant integration for **Aquastilla water softeners**. Also works on same device from Waterlife brand.
This integration logs in to the Aquastilla cloud, retrieves device data, and exposes it as sensors in Home Assistant.

> ⚠️ **Disclaimer**
> This is an **unofficial** integration. It is not affiliated with or endorsed by Aquastilla.

---

## ✨ Features

* 🔐 Secure login using Aquastilla account credentials
* 🚰 Real‑time water softener data
* 🧂 Salt level monitoring
* 💧 Daily water usage
* 🔄 Regeneration history & next expected regeneration
* 🌍 Multi‑language support (EN / PL)
* 🏠 Native Home Assistant config flow (UI setup)

---

## 📦 Installation

### Option 1: HACS (recommended)

1. Open **HACS** → **Integrations**
2. Search for **Aquastilla Softener** and install
3. Restart Home Assistant

### Option 2: Manual installation

1. Download or clone this repository
2. Copy the directory:

   ```text
   custom_components/aquastilla_softener
   ```

   into:

   ```text
   <config>/custom_components/
   ```
3. Restart Home Assistant

---

## ⚙️ Configuration

Configuration is done **entirely via the Home Assistant UI**.

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Aquastilla Softener**
4. Enter your **Aquastilla email and password**

> ℹ️ SSO / social logins are **not supported**.

---

## 📊 Entities

The integration exposes **multiple sensor entities** based on data returned by the Aquastilla cloud API.

### Main sensors

| Entity                                    | Description                |
| ----------------------------------------- | -------------------------- |
| `sensor.aquastilla_salt_level`            | Salt level                 |
| `sensor.aquastilla_available_water`       | Available softened water   |
| `sensor.aquastilla_water_usage_today`     | Water usage today          |
| `sensor.aquastilla_last_regeneration`     | Last regeneration date     |
| `sensor.aquastilla_expected_regeneration` | Expected regeneration date |

### Additional entities

Based on the current UI and API data, the following **additional sensors and controls** are exposed:

#### Sensors

| Entity                                    | Description                           |
| ----------------------------------------- | ------------------------------------- |
| `sensor.aquastilla_update_available`      | Firmware / data update availability   |
| `sensor.aquastilla_available_water`       | Available softened water (L)          |
| `sensor.aquastilla_water_usage_today`     | Water usage today (L)                 |
| `sensor.aquastilla_max_salt_days`         | Maximum number of salt days           |
| `sensor.aquastilla_expected_regeneration` | Expected regeneration date            |
| `sensor.aquastilla_last_regeneration`     | Last regeneration                     |
| `binary_sensor.aquastilla_connected`      | Cloud connection status               |
| `sensor.aquastilla_update_progress`       | Update progress (%)                   |
| `sensor.aquastilla_regeneration_progress` | Regeneration progress (%)             |
| `sensor.aquastilla_salt_level`            | Salt level (%)                        |
| `sensor.aquastilla_remaining_salt_days`   | Remaining salt days                   |
| `sensor.aquastilla_state`                 | Current device state (e.g. Softening) |

#### Controls

| Entity                                    | Description                                         |
| ----------------------------------------- | --------------------------------------------------- |
| `button.postpone_regeneration`            | Postpone regeneration(24h)                          |
| `switch.aquastilla_vacation_mode`         | Vacation mode                                       |
| `button.force_regeneration`               | Force regeneration now                              |
| `button.close_valve`                      | Close valve (open only possible directly on device) |

> ⚠️ Control entities may depend on API permissions and device firmware and may not be available on all accounts.

The integration auto-creates entities from available API fields, so the exact list may differ between installations and firmware versions.

---

## 🌐 Translations

Supported languages:

* 🇬🇧 English
* 🇵🇱 Polish

Translations are stored in:

```text
custom_components/aquastilla_softener/translations/
```

Pull requests for additional languages are welcome 🙌

---

## 🧪 Tested with

* Home Assistant Core 2024.x+
* Aquastilla cloud‑connected softeners

---

## 🚧 Known limitations

* Requires active internet connection
* Depends on Aquastilla cloud availability
* No local‑only API support

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

Please keep code formatted and follow Home Assistant integration guidelines.

---

## 📄 License

MIT License

---

## ☕ Support

Issues and feature requests can be reported via GitHub Issues.

If you find this project helpful, you can support me here:

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/alakdae)
