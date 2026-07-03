# 🗺️ Python Project Atlas Generator

**Project Atlas Generator** is a powerful static analysis tool for Python codebases. By parsing your project's Abstract Syntax Tree (AST), it automatically maps out modules, classes, methods, functions, and cross-references. It then compiles this structure into an interactive network of interlinked Markdown notes ready to be opened instantly as an Obsidian Vault!

With this tool, you can visualize and navigate your entire codebase directly inside the Obsidian Graph View, creating an intuitive visual "atlas" of your software architecture.

## ✨ Key Features

- 🗺️ **Auto-Generated Map of Content (MOC)**: Generates a central navigation hub (00_Project_MOC.md) listing all detected modules.

- 🌳 **AST-Based Structure Extraction:** Instantly extracts deep semantic information including classes, inherited base classes, functions, arguments, return type annotations, imports, and method lists.

- 🔗 **Wikilinks Connectivity:** Connects code definitions with automated ***[[Note_Name]]*** syntax to let you easily hop between nodes inside Obsidian.

- 🔄 **Calling Relationships & Backlinks:** Automatically tracks who calls whom. Method and function notes show what external objects they call, and who calls them (backlinks).

- 💻 **Seamless VS Code Integration:** Every note features a direct ***vscode://file/...*** hyperlink. Clicking it instantly opens the corresponding file in VS Code and jumps directly to the exact line of code.

- 📜 **Inline Source Code Previews:** For small functions or methods (under 20 lines of code), the generator embeds a syntax-highlighted Python block directly in the note.

- 📂 **Multi-file Project Clean-up:** Automatically clears out old visual graph structures on run to keep your notes perfectly in-sync with your newest commits.

## 🛠️ Global Installation & Setup (Windows)

You can set up the tool to run globally, allowing you to generate a structural map for any Python project with a single command from your terminal.

### Step 1: Create the Tool Directory

1. Create a dedicated folder on your system ***(e.g., C:\Tools\Atlas)***.

2. Save ***generate_atlas.py*** and ***atlas.bat*** inside this folder.

### Step 2: Add to System PATH

To trigger the generator from any directory:

1. Open the **Windows Start Menu**, type **Environment Variables**, and select **Edit the system environment variables**.

2. Click the **Environment Variables**... button at the bottom of the window.

3. Under User Variables (or System Variables), find the variable named **Path** and click **Edit**.

4. Click **New** and paste the path to your directory: ***C:\Tools\Atlas***.

5. Click OK on all windows to apply the changes.

Verify your installation by opening a new terminal window and running:
```python
python --version
```

## ⚙️ Project Configuration

The generator looks for a configuration file called .atlas_config in the root of your target project.

First Run Setup

On the first run inside a new project, the tool will automatically create a default .atlas_config file and prompt you to configure it:

```yml
"obsidian_vault_path": "C:\\obsidian\\YourVault\\Project_Atlas",
"ignore_dirs": [".obsidian", ".vscode", "__pycache__", "venv", ".git"]
```

| Parameter | Type | Description |
| :---------| :--- | :---------- |
| obsidian_vault_path | String | Absolute path to the Obsidian Vault (or subfolder within a Vault) where you want the nodes generated. |
| ignore_dirs | Array | Directories the scanner will completely skip (e.g., virtual environments, cache folders, and version control directories). |


## 🚀 How to Use

Once the folder is configured in your system **PATH**, generating your visual project map is as simple as running:

**Option A: Run directly inside the project root**

Open your terminal ***inside** your Python project's root* folder and type:
```
atlas
```

(The script automatically detects the current working directory as the project target.)

**Option B: Run by passing an explicit path**

You can also run the tool from anywhere by specifying the target directory:
```
atlas C:\Path\To\Your\Python\Project
```

## 📂 Output Directory Structure

The generator structures your target Obsidian directory with a neat system-specific taxonomy to keep files highly organized:
```
📁 Your_Obsidian_Vault/
└── 📁 graph/
    ├── 📄 00_Project_MOC.md          # Centrally linked Map of Content index
    ├── 📁 module/                    # Notes mapping file dependencies & module calls
    │   └── 📄 Module_subfolder_file_py.md
    ├── 📁 class/                     # Notes for detected classes (inheritance/methods)
    │   └── 📄 Class_ClassName.md
    ├── 📁 func/                      # Notes for standalone global functions
    │   └── 📄 Func_function_name.md
    └── 📁 method/                    # Notes for object-oriented class methods
        └── 📄 Method_ClassName_method_name.md
```

## 💡 Notes & Best Practices

**Skipping Files:** generate_atlas.py is always automatically skipped from its own analysis to prevent self-looping notes.

**Updating the Graph:** Simply re-run atlas inside your project directory at any time to recreate the folder structure and refresh your Obsidian notes.

*Graph example:*
![Node graph](.github\images\graph.png "Nodes graph" )

*Notes example:*

![Note example](.github\images\notes.png  "Note example")

**Graph View Viewport:** In order to see the graph in Obsidian, make sure to open a correct vault folder, enable the Graph View and adjust filters to group modules, classes, and methods by tags to get a beautifully clustered color-coded view of your codebase! 