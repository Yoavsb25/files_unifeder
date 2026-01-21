# GitHub Pages Deployment Guide

This guide explains how to deploy the PDF Merger UI to GitHub Pages.

## Prerequisites

- A GitHub repository
- GitHub Pages enabled in your repository settings

## Deployment Steps

### Option 1: Deploy from Root Directory (Recommended)

1. **Ensure files are in the root directory:**
   - `index.html`
   - `styles.css`
   - `app.js`
   - `.nojekyll` (already created)

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Navigate to **Settings** → **Pages**
   - Under **Source**, select **Deploy from a branch**
   - Choose **main** (or your default branch) and **/ (root)**
   - Click **Save**

3. **Your site will be available at:**
   ```
   https://[username].github.io/[repository-name]/
   ```

### Option 2: Deploy from `/docs` Directory

If you prefer to keep the UI files in a separate directory:

1. **Create a `docs` folder** in your repository root
2. **Move UI files to `docs/`:**
   ```bash
   mkdir docs
   mv index.html styles.css app.js .nojekyll docs/
   ```
3. **Enable GitHub Pages:**
   - Go to **Settings** → **Pages**
   - Select **Deploy from a branch**
   - Choose **main** and **/docs**
   - Click **Save**

## Important Notes

### Browser Limitations

Since this is a client-side application running in the browser:

1. **File Selection:** Users can select files and folders through the browser's file picker
2. **PDF Downloads:** Merged PDFs are automatically downloaded to the user's default download folder
3. **No Server Required:** All processing happens in the browser using JavaScript libraries

### Supported Browsers

- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

### File Size Limitations

- Large PDF files may take time to process
- Very large files (>100MB) may cause browser performance issues
- Consider processing files in smaller batches for best results

## Troubleshooting

### Files not loading correctly

- Ensure `.nojekyll` file exists in the root (or docs) directory
- Check that file paths in `index.html` are correct (relative paths)

### CDN Libraries not loading

- Check your internet connection
- Verify CDN URLs in `index.html` are accessible
- Consider downloading libraries locally if needed

### PDF merging fails

- Ensure PDF files are not corrupted
- Check browser console for error messages
- Verify that PDF-lib CDN is loading correctly

## Custom Domain (Optional)

To use a custom domain:

1. Add a `CNAME` file to your repository root with your domain name
2. Configure DNS settings with your domain provider
3. Update GitHub Pages settings to use your custom domain

## Updates

After making changes to the UI files:

1. Commit and push changes to your repository
2. GitHub Pages will automatically rebuild (may take a few minutes)
3. Hard refresh your browser (Cmd+Shift+R / Ctrl+Shift+R) to see updates
