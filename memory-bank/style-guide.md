# STYLE GUIDE: Mobile Phone Repair Service Website

## 🎨 BRAND OVERVIEW
**Business**: Mobile Phone Repair Service (Van-based, Orland Park, Illinois)
**Brand Personality**: Professional, Trustworthy, Accessible, Reliable, Local
**Target Audience**: Budget-conscious customers seeking convenient, on-site repair services
**Design Philosophy**: Clean, professional, mobile-first, conversion-focused

## 🌈 COLOR PALETTE

### Primary Colors
- **Navy Blue (Primary)**: `#1e3a5f` - Main brand color, headers, primary buttons
- **Pure White**: `#ffffff` - Background color, text on dark backgrounds
- **Bright Red (Accent)**: `#dc2626` - Call-to-action buttons, promotional elements, "$10 OFF"

### Secondary Colors
- **Light Navy**: `#2d4a6b` - Secondary buttons, hover states
- **Dark Navy**: `#152a42` - Text on light backgrounds, footer
- **Light Gray**: `#f8fafc` - Section backgrounds, subtle dividers
- **Medium Gray**: `#64748b` - Secondary text, placeholders
- **Dark Gray**: `#334155` - Body text, headings

### Status Colors
- **Success Green**: `#059669` - Success messages, completion states
- **Warning Orange**: `#d97706` - Warning messages, pending states
- **Error Red**: `#dc2626` - Error messages, validation issues
- **Info Blue**: `#0284c7` - Information messages, help text

### Promotional Colors
- **Promotion Red**: `#dc2626` - "$10 OFF" banners, special offers
- **Promotion Background**: `#fef2f2` - Light background for promotional sections

## 📝 TYPOGRAPHY

### Font Families
**Primary Font (Headings)**: 
- `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Modern, professional, highly readable

**Secondary Font (Body)**: 
- `'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Clean, readable, web-optimized

**Monospace (Technical)**: 
- `'JetBrains Mono', Consolas, 'Courier New', monospace`
- For phone numbers, technical specifications

### Font Sizes & Hierarchy
**Headings**:
- `h1`: 3rem (48px) - Page titles, hero headlines
- `h2`: 2.25rem (36px) - Section headers
- `h3`: 1.875rem (30px) - Subsection headers
- `h4`: 1.5rem (24px) - Component titles
- `h5`: 1.25rem (20px) - Card titles
- `h6`: 1.125rem (18px) - Small headers

**Body Text**:
- Large: 1.125rem (18px) - Important body text, descriptions
- Base: 1rem (16px) - Standard body text
- Small: 0.875rem (14px) - Secondary text, captions
- Extra Small: 0.75rem (12px) - Fine print, disclaimers

**Font Weights**:
- Light: 300
- Regular: 400
- Medium: 500
- Semi-bold: 600
- Bold: 700
- Extra Bold: 800

## 📐 SPACING SYSTEM

### Base Unit: 4px (0.25rem)

**Spacing Scale**:
- `xs`: 4px (0.25rem)
- `sm`: 8px (0.5rem)
- `md`: 16px (1rem)
- `lg`: 24px (1.5rem)
- `xl`: 32px (2rem)
- `2xl`: 48px (3rem)
- `3xl`: 64px (4rem)
- `4xl`: 96px (6rem)

**Component Spacing**:
- **Button Padding**: 12px 24px (vertical, horizontal)
- **Card Padding**: 24px
- **Section Padding**: 48px (desktop), 24px (mobile)
- **Container Max Width**: 1200px
- **Content Max Width**: 800px

## 🔘 BUTTON STYLES

### Primary Button (Call-to-Action)
```css
.btn-primary {
  background-color: #dc2626; /* Bright Red */
  color: #ffffff;
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background-color: #b91c1c;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}
```

### Secondary Button
```css
.btn-secondary {
  background-color: #1e3a5f; /* Navy Blue */
  color: #ffffff;
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background-color: #2d4a6b;
}
```

### Outline Button
```css
.btn-outline {
  background-color: transparent;
  color: #1e3a5f;
  padding: 12px 24px;
  border: 2px solid #1e3a5f;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-outline:hover {
  background-color: #1e3a5f;
  color: #ffffff;
}
```

## 📱 MOBILE-FIRST RESPONSIVE DESIGN

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

### Mobile Design Principles
- **Touch Targets**: Minimum 44px x 44px for touch elements
- **Thumb-Friendly**: Important actions within easy thumb reach
- **Progressive Disclosure**: Show essential info first, details on demand
- **Single Column Layout**: Stack elements vertically on mobile
- **Large Text**: Ensure readability without zooming

## 🎯 COMPONENT STYLES

### Card Component
```css
.card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  transition: all 0.2s ease;
}
```

### Form Input Styles
```css
.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #1e3a5f;
  box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1);
}

.form-input.error {
  border-color: #dc2626;
}
```

### Trust Signal Badges
```css
.trust-badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background-color: #f0f9ff;
  border: 1px solid #0284c7;
  border-radius: 20px;
  color: #0284c7;
  font-size: 0.875rem;
  font-weight: 500;
}
```

## 🎨 PROMOTIONAL ELEMENTS

### "$10 OFF" Banner Style
```css
.promo-banner {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  color: #ffffff;
  padding: 16px 24px;
  border-radius: 8px;
  text-align: center;
  font-weight: 700;
  font-size: 1.25rem;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
```

### Email Capture Popup
```css
.email-popup {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  text-align: center;
}
```

## 🗺️ SERVICE AREA MAP STYLING

### Map Container
```css
.map-container {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}

.map-overlay {
  position: absolute;
  top: 16px;
  left: 16px;
  background-color: rgba(30, 58, 95, 0.9);
  color: #ffffff;
  padding: 12px 16px;
  border-radius: 6px;
  font-weight: 600;
}
```

## 📊 DEVICE CATEGORY GRID

### Grid Layout
```css
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  padding: 24px 0;
}

.device-card {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  cursor: pointer;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: #1e3a5f;
}
```

## 🖼️ IMAGERY GUIDELINES

### Photo Style
- **Professional**: High-quality, well-lit photos
- **Authentic**: Real repair work, actual technician
- **Before/After**: Clear comparison shots
- **Branding**: Consistent lighting and backgrounds

### Icon Style
- **Line Icons**: Thin, consistent stroke width
- **Color**: Navy blue (#1e3a5f) for primary icons
- **Size**: 24px standard, 32px for important actions
- **Style**: Modern, minimal, professional

## 💬 TONE OF VOICE

### Brand Voice Characteristics
- **Professional but Approachable**: Expert knowledge presented simply
- **Trustworthy**: Honest, transparent communication
- **Local**: Community-focused, personal service
- **Confident**: Expertise without arrogance
- **Helpful**: Problem-solving oriented

### Content Guidelines
- **Headlines**: Direct, benefit-focused
- **Body Text**: Clear, concise, jargon-free
- **CTAs**: Action-oriented, urgent but not pushy
- **Error Messages**: Helpful, solution-focused

## ✅ ACCESSIBILITY GUIDELINES

### Color Contrast
- **Normal Text**: Minimum 4.5:1 contrast ratio
- **Large Text**: Minimum 3:1 contrast ratio
- **Interactive Elements**: Clear focus indicators

### Typography
- **Minimum Size**: 16px for body text
- **Line Height**: 1.5 minimum for readability
- **Font Weight**: Sufficient contrast for readability

### Interactive Elements
- **Focus States**: Visible focus indicators
- **Touch Targets**: Minimum 44px x 44px
- **Alt Text**: Descriptive alt text for images

## 🎯 CONVERSION OPTIMIZATION

### Call-to-Action Placement
- **Above the Fold**: Primary CTA visible immediately
- **Multiple Opportunities**: CTAs throughout the page
- **Progressive Disclosure**: Lead users through the booking funnel

### Trust Building Elements
- **Social Proof**: Customer testimonials, review counts
- **Credentials**: Certifications, warranties prominently displayed
- **Security**: Trust badges, secure payment indicators

## 📱 WORDPRESS THEME INTEGRATION

### Theme Customization Approach
- **Custom CSS**: Override theme styles with brand colors
- **Logo Integration**: Navy blue logo on white backgrounds
- **Menu Styling**: Consistent with button styles
- **Footer Design**: Dark navy background with white text

### Plugin Styling
- **Booking Forms**: Match form input styles
- **Payment Forms**: Consistent button and input styling
- **Contact Forms**: Brand-consistent appearance

This style guide ensures consistent, professional, and conversion-optimized design throughout the mobile phone repair service website while maintaining accessibility and mobile-first principles. 