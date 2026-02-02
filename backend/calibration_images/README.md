# Calibration Images

Place your calibration images in this folder. They will be automatically copied to the app's data directory on startup.

## Requirements

- **Format**: JPG or PNG
- **Recommended size**: 400x500 pixels
- **Naming convention**:
  - `male_1.jpg`, `male_2.jpg`, etc. for male portraits
  - `female_1.jpg`, `female_2.jpg`, etc. for female portraits
- **Recommended count**: 5 male + 5 female = 10 total

## How it works

1. Add your images to this folder
2. Commit and push to the repository
3. On deployment, the Dockerfile copies these to `/app/data/global_calibration/`
4. The calibration endpoint serves these images to users

## Example structure

```
calibration_images/
├── male_1.jpg
├── male_2.jpg
├── male_3.jpg
├── male_4.jpg
├── male_5.jpg
├── female_1.jpg
├── female_2.jpg
├── female_3.jpg
├── female_4.jpg
└── female_5.jpg
```

## Notes

- Images are served via `/api/calibration/images/{filename}`
- If no images are present, the app falls back to Unsplash URLs
- For best results, use high-quality portrait photos with clear faces
