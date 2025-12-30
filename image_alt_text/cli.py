#!/usr/bin/env python3
"""
Command-line interface for generating alt text from images using Claude AI.
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
    print("Error: anthropic package not installed.")
    print("Run: pip install anthropic")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow package not installed.")
    print("Run: pip install Pillow")
    sys.exit(1)

# ~3.5MB raw stays under 5MB after base64 encoding (+33% overhead)
MAX_IMAGE_SIZE = 3500000


def get_api_key() -> str | None:
    """Get API key from environment variable."""
    return os.environ.get("ANTHROPIC_API_KEY")


def get_media_type(file_path: str) -> str:
    """Get the MIME type based on file extension."""
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
    """
    Resize image if it exceeds the maximum size for the API.

    Returns:
        Tuple of (image_bytes, media_type)
    """
    file_size = os.path.getsize(image_path)
    media_type = get_media_type(image_path)

    if file_size <= MAX_IMAGE_SIZE:
        with open(image_path, "rb") as f:
            return f.read(), media_type

    print(f"Image is {file_size / 1024 / 1024:.1f}MB, resizing...")

    img = Image.open(image_path)

    # Convert to RGB if necessary (handles PNG transparency, palette images, etc.)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Progressively reduce quality and size until under limit
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
            # Return what we have as last resort
            return buffer.getvalue(), "image/jpeg"


def generate_alt_text(image_path: str) -> str:
    """
    Send image to Claude API and generate alt text.

    Args:
        image_path: Path to the image file

    Returns:
        Generated alt text string
    """
    image_bytes, media_type = resize_image_if_needed(image_path)
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    api_key = get_api_key()
    if not api_key:
        return "Error: ANTHROPIC_API_KEY environment variable not set. Please set your API key."

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
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
    """Create an HTML results page with the generated alt text."""
    image_name = Path(image_path).name
    # Escape HTML special characters in alt text
    escaped_alt = (alt_text
                   .replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;"))

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
            word-break: break-all;
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
        code {{
            background: #e9ecef;
            padding: 8px 12px;
            border-radius: 4px;
            display: block;
            margin-top: 8px;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Generated Alt Text</h1>
        <p class="image-name">File: {image_name}</p>

        <div class="alt-text-container">
            <p class="alt-text" id="altText">{escaped_alt}</p>
        </div>

        <button class="copy-btn" onclick="copyToClipboard()">Copy to Clipboard</button>

        <div class="instructions">
            <p><strong>Usage:</strong> Paste this alt text into your image's alt attribute:</p>
            <code>&lt;img src="..." alt="{escaped_alt}"&gt;</code>
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
    """Main entry point for the CLI."""
    if len(sys.argv) < 2:
        print("Image Alt Text Generator")
        print("=" * 40)
        print()
        print("Usage: image-alt-text <image_path>")
        print()
        print("Generates accessible alt text for images using Claude AI.")
        print()
        print("Setup:")
        print("  Set ANTHROPIC_API_KEY environment variable with your API key")
        print("  Get a key at: https://console.anthropic.com/")
        print()
        print("Windows Integration:")
        print("  Run 'image-alt-text-install' to add right-click menu option")
        print("  Run 'image-alt-text-uninstall' to remove it")
        sys.exit(0)

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

    webbrowser.open(f'file://{temp_path}')
    print("Opened result in browser")


if __name__ == "__main__":
    main()
