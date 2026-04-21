from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.cv.base import DetectionBox


def annotate_image(image_path: Path, boxes: list[DetectionBox], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        for box in boxes:
            draw.rectangle((box.x1, box.y1, box.x2, box.y2), outline=(21, 128, 61), width=4)
            label = f"person {box.confidence:.2f}" if box.confidence is not None else "person"
            text_bbox = draw.textbbox((box.x1, box.y1), label, font=font)
            draw.rectangle(text_bbox, fill=(21, 128, 61))
            draw.text((box.x1, box.y1), label, fill=(255, 255, 255), font=font)
        image.save(output_path)
    return output_path

