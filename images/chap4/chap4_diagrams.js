"use strict";

const path = require("path");
const PptxGenJS = require("pptxgenjs");
const { imageSizingContain } = require("./pptxgenjs_helpers/image");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers/layout");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "OpenAI";
pptx.subject = "Chapter 4 diagrams";
pptx.title = "Chapter 4 diagrams";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const BASE = path.resolve(__dirname, "..");
const OUT = path.join(BASE, "chap4_diagrams.pptx");

const IMAGE_STYLE = {};

const DIAGRAMS = [
  {
    stem: "cve_lifecycle",
    image: path.join(BASE, "cve_lifecycle.png"),
    box: { x: 1.28, y: 0.08, w: 10.78, h: 7.22 },
  },
  {
    stem: "data_flow_audit",
    image: path.join(BASE, "data_flow_audit.png"),
    box: { x: 1.08, y: 0.04, w: 11.18, h: 7.3 },
  },
  {
    stem: "role_use_case",
    image: path.join(BASE, "role_use_case.png"),
    box: { x: 0.16, y: 0.34, w: 13.0, h: 6.74 },
  },
  {
    stem: "storage_schema",
    image: path.join(BASE, "storage_schema.png"),
    box: { x: 0.08, y: 1.26, w: 13.15, h: 4.36 },
  },
  {
    stem: "strategy_code_flow",
    image: path.join(BASE, "strategy_code_flow.png"),
    box: { x: 0.96, y: 0.04, w: 11.4, h: 7.3 },
  },
];

function addBackground(slide) {
  slide.background = { color: "FFFFFF" };
}

function addDiagram(slide, item) {
  slide.addImage({
    path: item.image,
    ...imageSizingContain(item.image, item.box.x, item.box.y, item.box.w, item.box.h),
    ...IMAGE_STYLE,
  });
}

for (const item of DIAGRAMS) {
  const slide = pptx.addSlide();
  addBackground(slide);
  addDiagram(slide, item);
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

pptx.writeFile({ fileName: OUT });
