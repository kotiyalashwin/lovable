"use client"

import { javascript } from "@codemirror/lang-javascript";
import { oneDark } from "@codemirror/theme-one-dark";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import React from "react";

interface CodeEditorProps {
	code: string;
	onChange?: (newCode: string) => void;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({ code, onChange }) => {
    const transparentTheme = EditorView.theme({
    "&": {
      backgroundColor: "transparent !important",
    },
    ".cm-content": {
      caretColor: "#ffffff", // optional: make caret visible on transparent background
    },
    ".cm-scroller": {
      overflow: "auto", // ensure scrolling works
    },
  });
	return (
<CodeMirror
      value={code}
      height="100%"
      theme={[oneDark,transparentTheme]}
        width="100%"
      extensions={[javascript({ jsx: true, typescript: true })]}
      readOnly={true}
     
      basicSetup={{
        lineNumbers: true,
        highlightActiveLine: false,
        highlightActiveLineGutter: false,
      }}
      onChange={(value) => onChange?.(value)}
      className="rounded-lg bg-[#1c1c1c] overflow-scroll"
    />
	);
};
