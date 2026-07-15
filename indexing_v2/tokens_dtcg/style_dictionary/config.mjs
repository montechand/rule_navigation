// Checked-in Style Dictionary reference; the Python pipeline never executes this file.
const input = process.env.DESIGN_TOKENS_DIR ?? "design_tokens";

export default {
  source: [`${input}/tokens.base.json`, `${input}/modes/**/*.tokens.json`],
  platforms: {
    css: {
      transformGroup: "css",
      buildPath: "build/css/",
      files: [{ destination: "tokens.css", format: "css/variables" }],
    },
    scss: {
      transformGroup: "scss",
      buildPath: "build/scss/",
      files: [{ destination: "_tokens.scss", format: "scss/variables" }],
    },
    json: {
      transformGroup: "js",
      buildPath: "build/json/",
      files: [{ destination: "tokens.flat.json", format: "json/flat" }],
    },
  },
};
