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


## Marketplace 🛒

Browse and download community-created EFE extensions from the **EFE Market**:

➡️ **[EFE Market](https://github.com/OnyxNeol/EFE-Market)** — Community marketplace for EFE files

Submit your own EFE extensions, browse by category (creative, coding, knowledge, roleplay, tools), and share with the community. All submissions are auto-validated by the EGGUF scanner.

### Using Marketplace Extensions

```bash
# Download an EFE from the market, then apply it
python main.py apply model.egguf downloaded_extension.efe
```

### Contributing

1. Fork the [EFE Market repo](https://github.com/OnyxNeol/EFE-Market)
2. Add your `.efe` file to the appropriate category
3. Open a Pull Request — it's auto-validated

See [CONTRIBUTING.md](https://github.com/OnyxNeol/EFE-Market/blob/main/CONTRIBUTING.md) for details.

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

## Knowledge Database (Train with Your Data)

EGGUF supports embedding databases into the model so it can search through them when its built-in knowledge isn't enough. This is done through the `knowledge` API in EFE files.

### Supported Database Formats

| Format | Extensions | Description |
|--------|-----------|-------------|
| JSON | `.json` | Parsed as JSON objects/arrays |
| CSV | `.csv`, `.tsv` | Parsed into records (dict per row) |
| SQLite | `.db`, `.sqlite`, `.sqlite3` | All tables extracted as records |
| Text | `.txt`, `.md` | Parsed line-by-line as records |

### Loading a Database File

```python
# === EFE: My Knowledge Base ===

#use:You are a support assistant with access to the product database
from egguf_ext import knowledge

#use:You search through the AI/database if your knowledge doesn't contain the answer to the user
knowledge.database("products.json", description="Product catalog with prices and stock")

#use:You always cite which database record the answer came from
knowledge.search_if_unknown()
```

### Inline Database (No File Needed)

```python
# === EFE: Quick Knowledge ===

#use:You are a recipe assistant with a built-in recipe database
from egguf_ext import knowledge

#use:You search through the AI/database if your knowledge doesn't contain the answer to the user
knowledge.inline([
    {"name": "Pasta Carbonara", "ingredients": ["pasta", "eggs", "bacon"], "time": "20 min"},
    {"name": "Greek Salad", "ingredients": ["tomato", "feta", "olives"], "time": "10 min"}
], description="Recipe database")

#use:You always mention cooking time and ingredients when suggesting recipes
knowledge.search_if_unknown()
```

### How It Works

1. **`knowledge.database("file.json")`** — Loads and parses the file (JSON/CSV/SQLite/text)
2. **`knowledge.search_if_unknown()`** — Adds the "search if you don't know" instruction to the system prompt
3. **`knowledge.embed_context()`** — Converts the database to text and injects it into the model's context
4. **`knowledge.inline([...])`** — Use inline JSON data directly (no file needed)

The database data is embedded directly in the EGGUF extension, so the model can search through it at inference time. The `#use:` annotation on each `knowledge.*()` call becomes part of the system prompt, telling the model how to use the database.

### Sample Database Files

| Sample | Description |
|--------|-------------|
| `technova_support.efe` | Product catalog (JSON) with 15 products, support tickets, company info |
| `recipe_database.efe` | Inline recipe database (8 dishes, no external file needed) |
| `technova_database.json` | Sample JSON database for the TechNova support extension |
