# EGGUF — Extensible GGUF

Convert and extend GGUF models with the `#use:` system prompt framework.

## Quick Start

```bash
# Convert a GGUF model to EGGUF (adds the #use: system framework)
python gguf2egguf.py model.gguf

# Open the EGGUF file (GUI with popup: "Add extensions?")
python main.py open model.egguf

# Scan an EFE file (validate #use: annotations)
python main.py scan sample_extensions/creative_writer.efe

# Apply an EFE extension to an EGGUF
python main.py apply model.egguf sample_extensions/coding_assistant.efe

# Create your own EFE file
python main.py create-efe

# Publish .egguf and .efe file types to system registry
python publish_registry.py
```

## File Types

| Extension | Name | Description |
|-----------|------|-------------|
| `.egguf` | EGGUF Model File | Extensible GGUF — wraps a GGUF with the #use: extension framework |
| `.efe` | EFE Extension File | Extensions For EGGUF — Python code with #use: system prompt annotations |
| `.gguf` | GGUF Model File | Standard GGUF — can be converted to EGGUF |

## How #use: Works

The `#use:` annotation IS the system prompt. Every code line in an EFE file must have one:

```python
#use:You are a creative writing assistant with vivid imagery
from egguf_ext import params, response

#use:You generate with temperature 0.9 for creative output
params.temperature(0.9)

#use:You always format responses in markdown
response.markdown()
```

The scanner validates every code line has a `#use:` annotation before accepting the file.

## Building Executables

### GitHub Actions (automatic multi-platform builds)

Push to GitHub — the workflows in `.github/workflows/` will automatically build:

1. **`build.yml`** — Builds the `gguf2egguf` converter for Windows, macOS, and Linux
   - Triggers on: push to main, tags `v*`, manual dispatch
   - Tests each build with a mock GGUF
   - Creates a GitHub Release with all 3 executables when you push a `v*` tag

2. **`build-full-system.yml`** — Builds the full EGGUF system package for all 3 platforms
   - Triggers on: manual dispatch
   - Includes converter + main EGGUF system + registry publisher + samples
   - Creates a GitHub Release with zipped packages

### Local build

```bash
pip install pyinstaller
python build_exe.py --clean
```

## Publishing to Registry

```bash
# Windows (registers in HKEY_CLASSES_ROOT)
python publish_registry.py

# With custom paths
python publish_registry.py --python "C:\Python311\python.exe" --egguf-dir "C:\EGGUF"
```

Registers:
- `.egguf` → EGGUF Model File (Open, Apply EFE, Export, Info)
- `.efe` → EFE Extension File (Open Creator, Scan)
- `.gguf` → "Convert to EGGUF" context menu option

## Project Structure

```
egguf-system/
├── .github/workflows/
│   ├── build.yml                 # Build converter exe (Win/Mac/Linux)
│   └── build-full-system.yml     # Build full system package
├── gguf2egguf.py                 # Standalone converter (→ exe)
├── main.py                       # Full EGGUF system entry point
├── egguf_format.py               # EGGUF binary format (read/write)
├── efe_format.py                 # EFE format (read/execute)
├── scanner.py                    # #use: validation scanner
├── egguf_ext.py                  # EFE extension API (params, behavior, etc.)
├── extensions.py                 # Extension application logic
├── converter.py                  # GGUF ↔ EGGUF conversion
├── gui.py                        # EGGUF GUI (popup dialog)
├── efe_creator.py                # EFE file creator GUI
├── publish_registry.py           # Publish file types to registry
├── build_exe.py                  # Local PyInstaller build script
├── install.py                    # Installer script
├── sample_extensions/            # Sample EFE files
│   ├── creative_writer.efe
│   ├── coding_assistant.efe
│   ├── medical_knowledge.efe
│   ├── wise_wizard_roleplay.efe
│   ├── translator.efe
│   ├── smart_search_assistant.efe
│   └── _bad_missing_use.efe       # Test file (should fail scanner)
└── requirements.txt
```

## License

MIT
