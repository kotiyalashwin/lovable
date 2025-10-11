'use client';

import { useState } from 'react';
import Chat from "@/components/chat";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { CodeViewer } from "@/components/viewer/viewer";
import { Loader } from '../custom-loader';

interface ChatWithCodeViewerProps {
  projectId: string;
}

export default function ChatWithCodeViewer({ projectId }: ChatWithCodeViewerProps) {
  const [isSocketConnected, setIsSocketConnected] = useState(false);

  return (
    <div className="h-screen w-screen bg-neutral-900 text-white">
      <ResizablePanelGroup direction="horizontal">
        {/* Left panel */}
        <ResizablePanel className="min-h-screen" defaultSize={30} minSize={10} maxSize={90}>
          <Chat 
            projectId={projectId} 
            onSocketConnect={() => setIsSocketConnected(true)}
          />
        </ResizablePanel>
        {/* Handle */}
        <ResizableHandle withHandle/>
        {/* Right panel */}
        <ResizablePanel>
          {isSocketConnected ? (
            <CodeViewer projectId={projectId} />
          ) : (
            <div className="flex items-center justify-center h-full text-neutral-500">
              <Loader variant='gradient'/>
            </div>
          )}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
