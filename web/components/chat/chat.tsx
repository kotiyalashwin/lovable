"use client";

import { ChevronRight, CircleCheck } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import CreatedMessage from "./created";
import Thinking from "./thinking";
import Terminal from "./terminal";

type ChatType = "user" | "ai";

interface ChatMessage {
	id: string;
	type: ChatType;
	message: string;
	event?: "thinking" | "started" | "file_created" | "completed" | "command";
}

export default function Chat({
	projectId,
	onSocketConnect,
    changePrompt
}: {
    changePrompt:(value:string)=> void
	projectId: string;
	onSocketConnect: (value:boolean) => void;
}) {
	const prompt = localStorage.getItem("prompt") ?? "";
	const [chats, setChats] = useState<ChatMessage[]>([
		{ id: "1", type: "user", message: prompt },
	]);
	const [input, setInput] = useState("");
	const chatEndRef = useRef<HTMLDivElement>(null);

	// Scroll to bottom whenever chats update
	useEffect(() => {
		chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
	});

	// Connect to WebSocket
	useEffect(() => {
	  const ws = new WebSocket(`ws://localhost:8000/ws/${projectId}`); // replace with your server URL

	  ws.onopen = () => {
	    console.log("WebSocket connected");
	    onSocketConnect(true)
	  };

	  ws.onmessage = (event) => {
	    try {
	      const data: { e: "started" | "file_created" | "completed" | "thinking" | "command" ; message: string } = JSON.parse(
	        event.data
	      );

	      setChats((prev) => {
	        let updated = [...prev];

	        // Remove any existing "started" messages if event is "update"
	        if (data.e === "file_created" || data.e === "command") {
	          updated = updated.filter((msg) => msg.event !== "started");
	        }

	        // Add new AI message
	        updated.push({
	          id: Date.now().toString(),
	          type: "ai",
	          message: data.message,
	          event: data.e,
	        });

	        return updated;
	      });
	    } catch (err) {
	      console.error("Failed to parse WebSocket message", err);
	    }
	  };

	  ws.onclose = () => {
	    console.log("WebSocket disconnected");
	  };

	  return () => ws.close();
	}, [projectId,onSocketConnect]);

	const handleSend = () => {
		if (!input.trim()) return;

		const newUserMessage: ChatMessage = {
			id: Date.now().toString(),
			type: "user",
			message: input,
		};

		setChats((prev) => [...prev, newUserMessage]);
        changePrompt(input)
		setInput("");
	};
	const getChatComponent = (type: string, message: string, action?: string) => {
		switch (type) {
			case "ai":
				switch (action) {
					case "thinking":
						return <Thinking message={message} />;
					case "file_created":
						return <CreatedMessage message={message} />;
                    case "started":
                        return <div className="text-neutral-400 px-4 animate-pulse text-xl">Creating Project...</div>
                    case "command":
                        return <Terminal command={message}/>
                    
				}
			case "user":
				return (
					<div className="max-w-[70%] px-4 py-2 rounded-lg break-words flex items-center gap-2 bg-[#272825] text-white rounded-tr-none text-lg">
						{" "}
						{message}{" "}
					</div>
				);
		}
	};
	return (
		<div className="h-full flex bg-[#1c1c1c] flex-col text-white">
			<h1 className="text-xl mb-4 p-4">Conversation..</h1>

			{/* Chat container */}
			<div className="flex-1 border-t overflow-y-auto p-4 space-y-4">
				{chats.map((chat) => (
					<div
						key={chat.id}
						className={`flex ${chat.type === "user" ? "justify-end" : "justify-start"}`}
					>
						{getChatComponent(chat.type, chat.message, chat.event)}
					</div>
				))}
				<div ref={chatEndRef} />
			</div>

			<div className="p-4 flex items-center gap-4 mb-10">
						<Input
							placeholder="Type your message..."
							value={input}
							onChange={(e) => setInput(e.target.value)}
							className="flex-1 bg-transparent border-none text-white placeholder:text-neutral-400 focus:ring-0 focus:border-none"
							onKeyDown={(e) => {
								if (e.key === "Enter") handleSend();
							}}
						/>
						<button
							type="button"
							onClick={handleSend}
							className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1 rounded-lg transition"
						>
							Send
						</button>
			</div>
		</div>
	);
}
