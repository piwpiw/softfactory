/**
 * Icon Generator for SoftFactory PWA
 * Generates placeholder SVG icons in various sizes
 * Can be replaced with actual PNG files later
 *
 * Usage: node generate-icons.js
 */

const fs = require('fs');
const path = require('path');

const ICON_SIZES = [
  { size: 192, name: 'icon-192x192' },
  { size: 512, name: 'icon-512x512' },
  { size: 180, name: 'icon-180x180' }
];

const ICON_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <!-- Background gradient -->
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e293b;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="512" height="512" fill="url(#grad)" rx="100"/>

  <!-- Factory icon -->
  <g transform="translate(90, 100)" fill="none" stroke="white" stroke-width="20" stroke-linecap="round" stroke-linejoin="round">
    <!-- Building -->
    <rect x="10" y="80" width="280" height="200" rx="10"/>

    <!-- Windows -->
    <rect x="30" y="100" width="40" height="40" rx="5" fill="white" opacity="0.3"/>
    <rect x="90" y="100" width="40" height="40" rx="5" fill="white" opacity="0.3"/>
    <rect x="150" y="100" width="40" height="40" rx="5" fill="white" opacity="0.3"/>
    <rect x="210" y="100" width="40" height="40" rx="5" fill="white" opacity="0.3"/>

    <rect x="30" y="170" width="40" height="40" rx="5" fill="white" opacity="0.3"/>
    <rect x="90" y="170" width="40" height="40" rx="5" fill="white" opacity="0.3"/>
    <rect x="150" y="170" width="40" height="40" rx="5" fill="white" opacity="0.3"/>
    <rect x="210" y="170" width="40" height="40" rx="5" fill="white" opacity="0.3"/>

    <!-- Smokestacks -->
    <rect x="50" y="20" width="25" height="70" rx="12" fill="none" stroke="white" stroke-width="20"/>
    <rect x="225" y="20" width="25" height="70" rx="12" fill="none" stroke="white" stroke-width="20"/>

    <!-- Smoke clouds -->
    <circle cx="62" cy="10" r="12" fill="white" opacity="0.6"/>
    <circle cx="75" cy="5" r="10" fill="white" opacity="0.5"/>
    <circle cx="237" cy="10" r="12" fill="white" opacity="0.6"/>
    <circle cx="250" cy="5" r="10" fill="white" opacity="0.5"/>
  </g>

  <!-- Badge circle in corner -->
  <circle cx="420" cy="420" r="70" fill="#22c55e" opacity="0.9"/>
  <text x="420" y="435" font-size="60" font-weight="bold" text-anchor="middle" fill="white" font-family="Arial">✓</text>
</svg>
`;

/**
 * Convert SVG to PNG using canvas (would require additional libraries)
 * For now, we'll create SVG files that can be served as images
 */
function generateIcons() {
  const iconDir = path.join(__dirname, 'icons');

  // Create icons directory if it doesn't exist
  if (!fs.existsSync(iconDir)) {
    fs.mkdirSync(iconDir, { recursive: true });
    console.log(`Created directory: ${iconDir}`);
  }

  // Generate SVG icons for each size
  ICON_SIZES.forEach(({ size, name }) => {
    const filename = path.join(iconDir, `${name}.svg`);
    fs.writeFileSync(filename, ICON_SVG);
    console.log(`Generated: ${filename}`);
  });

  // Generate screenshot placeholders
  const screenshots = [
    { width: 540, height: 720, name: 'screenshot-540x720.svg' },
    { width: 1280, height: 720, name: 'screenshot-1280x720.svg' }
  ];

  screenshots.forEach(({ width, height, name }) => {
    const screenshotSvg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}">
        <defs>
          <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#1e293b;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1" />
          </linearGradient>
        </defs>
        <rect width="${width}" height="${height}" fill="url(#grad)"/>
        <text x="${width/2}" y="${height/2}" font-size="48" text-anchor="middle" fill="white" font-family="Arial">SoftFactory Dashboard</text>
      </svg>
    `;

    const filename = path.join(iconDir, name);
    fs.writeFileSync(filename, screenshotSvg);
    console.log(`Generated: ${filename}`);
  });

  console.log('\n✓ All icons generated successfully!');
  console.log('Note: These are SVG files. For production, convert to PNG using:');
  console.log('  npm install svg2png');
  console.log('  Then update the manifest.json to reference .png files');
}

// Run generator
if (require.main === module) {
  generateIcons();
}

module.exports = { generateIcons };
