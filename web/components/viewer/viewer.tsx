"use client";
import axios from "axios";
import { useEffect, useState } from "react";
import { Loader } from "../custom-loader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { CodeEditor } from "./code";
import { FileExplorer } from "./explorer";

type FileType = {
	file_path: string; // e.g., "package.json", "src/app.jsx"
	content: string; // content with \n included
};

export type FileNode = {
	name: string;
	path: string; // full path
	children?: FileNode[];
	isFile: boolean;
	content?: string;
};

function buildFileTree(files: FileType[]): FileNode[] {
	const root: Record<string, any> = {};

	for (const file of files) {
		const parts = file.file_path.split("/");
		let current = root;

		for (let i = 0; i < parts.length; i++) {
			const part = parts[i];

			if (!current[part]) {
				current[part] = {
					name: part,
					path: parts.slice(0, i + 1).join("/"),
					children: {},
					isFile: i === parts.length - 1,
				};
				if (i === parts.length - 1) current[part].content = file.content;
			}

			current = current[part].children;
		}
	}

	// Convert nested objects to array recursively
	function objectToArray(obj: any): FileNode[] {
		return Object.values(obj).map((node: any) => ({
			name: node.name,
			path: node.path,
			isFile: node.isFile,
			content: node.content,
			children: node.children ? objectToArray(node.children) : [],
		}));
	}

	return objectToArray(root);
}

export const CodeViewer: React.FC<{ projectId: string,prompt:string }> = ({
	projectId, prompt
}: {
	projectId: string;
    prompt:string
}) => {
	const [tree, setTree] = useState<FileNode[]>([]);
	const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
	// useEffect(() => {
	//   setTree(buildFileTree(files));
	// }, [files])
    const [prevUrl, setPrevUrl]= useState<string | null>(null)
	useEffect(() => {
        setTree([])
		axios
			.post(`http://localhost:8000/chat/${projectId}`, {
				prompt: prompt,
			})
			.then((res) => {
				const data = res.data;
				const files: FileType[] = data.files;
				const treeFiles = buildFileTree(files);
                const prevUrl = `https://5173-${data.sandbox_id}.e2b.app`
                setPrevUrl(prevUrl)
				setTree(treeFiles);
				setSelectedFile(treeFiles[0]);
			});
	}, [projectId,prompt]);
	return (
		<div className="flex w-full h-screen">
			{tree.length === 0 ? (
				<div className="flex justify-center h-full w-full">
					<Loader variant="square" message="Building your MVP..." />
				</div>
			) : (
				<>
					{" "}
					<div
						style={{
							width: "300px",
							overflowY: "auto",
							borderRight: "1px solid #ccc",
						}}
					>
						<FileExplorer files={tree} onFileClick={setSelectedFile} />
					</div>
					{/* <div style={{ flex: 1, padding: "10px" }}> */}
					{/* 	{selectedFile && <CodeEditor code={selectedFile.content || ""} />} */}
					{/* </div> */}
					<div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
						<Tabs defaultValue="code" className="flex-1 flex flex-col">
							<TabsList>
								<TabsTrigger value="code">Code Viewer</TabsTrigger>
                                <TabsTrigger value="preview" className={prevUrl ? "":"disabled"}>Preview</TabsTrigger>
							</TabsList>

							<TabsContent value="code" className="flex-1 overflow-auto p-4">
								{selectedFile ? (
									<CodeEditor code={selectedFile.content || ""} />
								) : (
									<div>Select a file to view code</div>
								)}
							</TabsContent>

							<TabsContent
								value="preview"
								className="flex-1 overflow-hidden flex justify-center items-center"
							>
								<iframe
									src={prevUrl ?? ""}
									title="Preview"
									style={{
										width: "100%",
										height: "100%",
										border: "none",
									}}
								/>{" "}
							</TabsContent>
						</Tabs>
					</div>
				</>
			)}
		</div>
	);
};
