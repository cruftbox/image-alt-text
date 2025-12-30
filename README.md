# Image Alt Text Generator

Generate accessible alt text for images using Claude AI, with Windows Explorer right-click integration.

## What It Does

This tool uses Anthropic's Claude AI to automatically generate descriptive alt text for images. Alt text is essential for:

- **Accessibility**: Screen readers use alt text to describe images to visually impaired users
- **SEO**: Search engines use alt text to understand image content
- **Fallback**: Alt text displays when images fail to load

### Features

- **One-click generation**: Right-click any image in Windows Explorer to generate alt text
- **Browser-based results**: Opens a clean webpage with the generated alt text and a copy button
- **Automatic image resizing**: Handles large images by automatically compressing them to fit API limits
- **Multiple formats**: Supports JPG, JPEG, PNG, GIF, and WebP images

## How It Works

1. You right-click an image file in Windows Explorer
2. Select "Generate Alt Text" from the context menu
3. The tool sends the image to Claude AI via Anthropic's API
4. Claude analyzes the image and generates concise, descriptive alt text
5. A browser window opens displaying the alt text with a copy button

The generated alt text follows accessibility best practices:
- Concise (1-2 sentences)
- Descriptive of key visual elements
- Doesn't start with "Image of" or "Picture of"
- Suitable for screen readers

## Requirements

- **Windows 10 or 11**
- **Python 3.10 or higher**
- **Anthropic API key** (get one at [console.anthropic.com](https://console.anthropic.com/))

## Installation

### Step 1: Install the Package

```bash
pip install image-alt-text
```

Or install from source:

```bash
git clone https://github.com/cruftbox/image-alt-text.git
cd image-alt-text
pip install .
```

### Step 2: Set Your API Key

Set the `ANTHROPIC_API_KEY` environment variable:

**Option A: Via Windows Settings (Recommended - Permanent)**

1. Press `Win + S` and search for "environment variables"
2. Click "Edit the system environment variables"
3. Click "Environment Variables..."
4. Under "User variables", click "New..."
5. Variable name: `ANTHROPIC_API_KEY`
6. Variable value: `your-api-key-here`
7. Click OK and restart any open terminals

**Option B: Via Command Line (Temporary)**

```bash
# Command Prompt
set ANTHROPIC_API_KEY=your-api-key-here

# PowerShell
$env:ANTHROPIC_API_KEY = "your-api-key-here"
```

### Step 3: Install Windows Integration

Run the installer to add the right-click context menu:

```bash
image-alt-text-install
```

This adds "Generate Alt Text" to the right-click menu for image files.

## Usage

### Via Right-Click Menu

1. Right-click any image file (JPG, PNG, GIF, WebP)
2. Click "Generate Alt Text"
   - On Windows 11: You may need to click "Show more options" first
3. Wait a few seconds for Claude to analyze the image
4. A browser window opens with the generated alt text
5. Click "Copy to Clipboard" to copy the text

### Via Command Line

```bash
image-alt-text path/to/image.jpg
```

## Windows 11 Context Menu Note

Windows 11 uses a simplified right-click menu by default. The "Generate Alt Text" option appears under "Show more options".

To always show the full context menu (recommended), you can enable the classic menu:

1. Open the folder containing this package
2. Double-click `enable_classic_context_menu.reg`
3. Confirm the registry change
4. Restart Explorer or reboot

To revert to Windows 11's modern menu, run `disable_classic_context_menu.reg`.

## Uninstallation

Remove the Windows integration:

```bash
image-alt-text-uninstall
```

Uninstall the package:

```bash
pip uninstall image-alt-text
```

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"

Make sure you've set the API key as described in Step 2 above. If you set it via Windows Settings, you need to restart your terminal or Explorer.

### "Image exceeds 5 MB maximum"

The tool automatically resizes large images, but if you see this error, the image may be extremely large. Try with a smaller image or a different format.

### Context menu doesn't appear

1. Make sure you ran `image-alt-text-install`
2. On Windows 11, try clicking "Show more options"
3. Try restarting Explorer: `taskkill /f /im explorer.exe && start explorer.exe`

### "No module named 'anthropic'"

Install the required dependencies:

```bash
pip install anthropic Pillow
```

## API Costs

This tool uses Claude's API, which has associated costs. Each image analysis typically uses a small number of tokens. Check [Anthropic's pricing](https://www.anthropic.com/pricing) for current rates.

## Privacy

- Images are sent to Anthropic's API for analysis
- No images are stored locally or remotely by this tool
- Review [Anthropic's privacy policy](https://www.anthropic.com/privacy) for details on API data handling

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.
