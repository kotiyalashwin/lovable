
import Chat from "@/components/chat";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { CodeViewer } from "@/components/viewer/viewer";

export default async function Page({params}:{params : {id:string}}) {
    const projectId = (await params).id
  return (
    <div className="h-screen w-screen bg-neutral-900 text-white">
      <ResizablePanelGroup direction="horizontal">
        {/* Left panel */}
        <ResizablePanel className="min-h-screen" defaultSize={30} minSize={10} maxSize={90}>
          <Chat projectId={projectId}/>
        </ResizablePanel>

        {/* Handle */}
        <ResizableHandle withHandle/>

        {/* Right panel */}
        <ResizablePanel>
          {/* <Code/> */}
        <CodeViewer projectId={projectId}/>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

