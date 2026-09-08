/* Obsidian Kinetic — design tokens.
   Loaded after the Tailwind CDN script so the CDN picks the config up. */
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "tertiary": "#eafff0", "on-tertiary-fixed-variant": "#005236",
        "on-secondary-fixed-variant": "#5516be", "error": "#ffb4ab",
        "secondary-container": "#571bc1", "on-tertiary": "#003824",
        "on-secondary-fixed": "#23005c", "tertiary-container": "#69f6b9",
        "background": "#131317", "surface-dim": "#131317",
        "secondary-fixed-dim": "#d0bcff", "on-surface": "#e5e1e7",
        "primary-container": "#00f5ff", "on-primary": "#003739",
        "error-container": "#93000a", "on-primary-container": "#006c71",
        "inverse-primary": "#00696e", "secondary-fixed": "#e9ddff",
        "surface-tint": "#00dce5", "surface-variant": "#353439",
        "on-primary-fixed-variant": "#004f53", "inverse-surface": "#e5e1e7",
        "surface-container-lowest": "#0e0e12", "tertiary-fixed": "#6ffbbe",
        "primary-fixed": "#63f7ff", "on-tertiary-container": "#006f4c",
        "on-surface-variant": "#b9caca", "surface-container": "#1f1f23",
        "on-primary-fixed": "#002021", "primary": "#e9feff",
        "on-secondary-container": "#c4abff", "outline-variant": "#3a494a",
        "on-error": "#690005", "surface-container-highest": "#353439",
        "surface": "#131317", "on-background": "#e5e1e7",
        "on-secondary": "#3c0091", "tertiary-fixed-dim": "#4edea3",
        "surface-container-high": "#2a292e", "surface-bright": "#39393d",
        "on-error-container": "#ffdad6", "secondary": "#d0bcff",
        "inverse-on-surface": "#303034", "primary-fixed-dim": "#00dce5",
        "on-tertiary-fixed": "#002113", "surface-container-low": "#1b1b1f",
        "outline": "#849495"
      },
      borderRadius: { DEFAULT: "0.125rem", lg: "0.25rem", xl: "0.5rem", full: "0.75rem" },
      spacing: {
        "gutter-desktop": "2rem", "gutter-mobile": "1rem", "container-max": "1200px",
        "space-3xs": "0.125rem", "space-2xs": "0.25rem", "space-xs": "0.5rem",
        "space-sm": "0.75rem", "space-md": "1rem", "space-lg": "1.5rem",
        "space-xl": "2rem", "space-2xl": "3rem", "space-3xl": "4rem",
        "space-4xl": "6rem", "space-5xl": "8rem"
      },
      fontFamily: {
        "label-code-md": ["JetBrains Mono"], "label-code-sm": ["JetBrains Mono"],
        "display-hero": ["Geist"], "display-hero-mobile": ["Geist"],
        "headline-xl": ["Geist"], "headline-xl-mobile": ["Geist"],
        "headline-lg": ["Geist"], "headline-md": ["Geist"], "headline-sm": ["Geist"],
        "body-lg": ["Geist"], "body-md": ["Geist"], "body-sm": ["Geist"]
      },
      fontSize: {
        "label-code-md": ["13px", { lineHeight: "18px", letterSpacing: "-0.01em", fontWeight: "400" }],
        "label-code-sm": ["11px", { lineHeight: "16px", letterSpacing: "0.04em", fontWeight: "500" }],
        "display-hero": ["72px", { lineHeight: "80px", letterSpacing: "-0.04em", fontWeight: "600" }],
        "display-hero-mobile": ["40px", { lineHeight: "48px", letterSpacing: "-0.03em", fontWeight: "600" }],
        "headline-xl": ["48px", { lineHeight: "56px", letterSpacing: "-0.03em", fontWeight: "600" }],
        "headline-xl-mobile": ["32px", { lineHeight: "40px", letterSpacing: "-0.025em", fontWeight: "600" }],
        "headline-lg": ["32px", { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "500" }],
        "headline-md": ["24px", { lineHeight: "32px", letterSpacing: "-0.015em", fontWeight: "500" }],
        "headline-sm": ["18px", { lineHeight: "26px", letterSpacing: "-0.01em", fontWeight: "500" }],
        "body-lg": ["16px", { lineHeight: "26px", letterSpacing: "-0.005em", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "22px", letterSpacing: "0em", fontWeight: "400" }],
        "body-sm": ["12px", { lineHeight: "18px", letterSpacing: "0.01em", fontWeight: "400" }]
      }
    }
  }
};
