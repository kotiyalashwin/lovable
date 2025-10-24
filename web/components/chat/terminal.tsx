import { ChevronRight } from "lucide-react";
import * as motion from "motion/react-client";
import { TerminalIcon } from "lucide-react";
export default function Terminal({ command }: { command: string }) {
  return (
    <motion.div
      initial={{ x: -10, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.25 }}
      className="bg-gradient-to-br  flex-col from-neutral-900/50 overflow-hidden to-neutral-900/70 border-2 border-neutral-800  rounded-xl shadow-2xl   font-mono text-sm tracking-wide flex items-center space-x-2"
    >
        <p className=" float-start w-full border-b px-4 py-1"><TerminalIcon className="text-neutral-400"/></p>

      <motion.span
        initial={{ opacity: 0.4 }}
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 2.5, repeat: 2, ease: "easeInOut" }}
        className="text-neutral-200 italic p-4"
      >
        {command}
      </motion.span>
    </motion.div>
  );
}

