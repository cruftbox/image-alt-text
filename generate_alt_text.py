#!/usr/bin/env python3
"""
Generate alt text for images using Claude API.
Right-click context menu integration for Windows 11.
"""

import sys
import base64
import webbrowser
import tempfile
import os
import io
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Please install the anthropic package: pip install anthropic")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Please install Pillow for image resizing: pip install Pillow")
    sys.exit(1)

MAX_IMAGE_SIZE = 3500000  # ~3.5MB raw to stay under 5MB after base64 encoding (+33% overhead)

# Set your API key here or use environment variable ANTHROPIC_API_KEY
API_KEY = "YOUR_API_KEY_HERE"

def get_media_type(file_path: str) -> str:
    """Get the media type based on file extension."""
    ext = Path(file_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return media_types.get(ext, "image/jpeg")

def resize_image_if_needed(image_path: str) -> tuple[bytes, str]:
    """Resize image if it exceeds the maximum size. Returns (image_bytes, media_type)."""
    file_size = os.path.getsize(image_path)
    media_type = get_media_type(image_path)

    if file_size <= MAX_IMAGE_SIZE:
        with open(image_path, "rb") as f:
            return f.read(), media_type

    print(f"Image is {file_size / 1024 / 1024:.1f}MB, resizing...")

    img = Image.open(image_path)

    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Progressively reduce size until under limit
    quality = 85
    scale = 1.0

    while True:
        if scale < 1.0:
            new_size = (int(img.width * scale), int(img.height * scale))
            resized = img.resize(new_size, Image.Resampling.LANCZOS)
        else:
            resized = img

        buffer = io.BytesIO()
        resized.save(buffer, format='JPEG', quality=quality, optimize=True)

        if buffer.tell() <= MAX_IMAGE_SIZE:
            print(f"Resized to {buffer.tell() / 1024 / 1024:.1f}MB")
            return buffer.getvalue(), "image/jpeg"

        if quality > 60:
            quality -= 10
        else:
            scale -= 0.1
            quality = 85

        if scale < 0.2:
            return buffer.getvalue(), "image/jpeg"

def get_api_key() -> str | None:
    """Resolve the Anthropic API key.

    Order: hardcoded API_KEY (if set) -> on Windows, the User-level
    ANTHROPIC_API_KEY read directly from the registry -> the process
    environment.

    The registry is preferred over the process environment on Windows
    because programs launched from Explorer inherit Explorer's environment,
    which is a snapshot from when Explorer started (usually last sign-in).
    After rotating the key, that snapshot still holds the OLD value, so
    trusting os.environ first would feed a revoked key to the API. The
    registry always reflects the current persisted user value.
    """
    if API_KEY != "YOUR_API_KEY_HERE":
        return API_KEY

    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg_key:
                value, _ = winreg.QueryValueEx(reg_key, "ANTHROPIC_API_KEY")
                if value:
                    return value
        except OSError:
            pass

    return os.environ.get("ANTHROPIC_API_KEY") or None


def generate_alt_text(image_path: str) -> str:
    """Send image to Claude and get alt text."""
    image_bytes, media_type = resize_image_if_needed(image_path)
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    api_key = get_api_key()
    if not api_key:
        return "Error: No API key found. Set ANTHROPIC_API_KEY environment variable or edit the script."

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Generate concise, descriptive alt text for this image. The alt text should:
- Be 1-2 sentences maximum
- Describe the key visual elements and context
- Be suitable for screen readers
- Not start with "Image of" or "Picture of"

Respond with ONLY the alt text, no additional explanation."""
                    }
                ],
            }
        ],
    )

    return message.content[0].text

def create_html_page(alt_text: str, image_path: str) -> str:
    """Create an HTML page displaying the alt text."""
    image_name = Path(image_path).name

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alt Text Generator - Result</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 32px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-top: 0;
            font-size: 24px;
        }}
        .image-name {{
            color: #666;
            font-size: 14px;
            margin-bottom: 24px;
        }}
        .alt-text-container {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .alt-text {{
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            margin: 0;
        }}
        .copy-btn {{
            background: #0066cc;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .copy-btn:hover {{
            background: #0052a3;
        }}
        .copy-btn.copied {{
            background: #28a745;
        }}
        .instructions {{
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid #e9ecef;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Generated Alt Text</h1>
        <p class="image-name">File: {image_name}</p>

        <div class="alt-text-container">
            <p class="alt-text" id="altText">{alt_text}</p>
        </div>

        <button class="copy-btn" onclick="copyToClipboard()">Copy to Clipboard</button>

        <div class="instructions">
            <p><strong>Usage:</strong> Paste this alt text into your image's alt attribute:</p>
            <code>&lt;img src="..." alt="{alt_text}"&gt;</code>
        </div>
    </div>

    <script>
        function copyToClipboard() {{
            const altText = document.getElementById('altText').innerText;
            navigator.clipboard.writeText(altText).then(() => {{
                const btn = document.querySelector('.copy-btn');
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {{
                    btn.textContent = 'Copy to Clipboard';
                    btn.classList.remove('copied');
                }}, 2000);
            }});
        }}
    </script>
</body>
</html>'''

    return html

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_alt_text.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    print(f"Generating alt text for: {image_path}")

    try:
        alt_text = generate_alt_text(image_path)
    except Exception as e:
        alt_text = f"Error generating alt text: {str(e)}"

    html_content = create_html_page(alt_text, image_path)

    # Save HTML to temp file and open in browser
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name

    webbrowser.open(Path(temp_path).as_uri())
    print(f"Opened result in browser")

if __name__ == "__main__":
    main()
