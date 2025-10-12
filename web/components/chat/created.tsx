import { ChevronRight } from "lucide-react";
import * as motion from "motion/react-client"
export default function CreatedMessage({ message }: { message: string }) {
	return (
		
			<motion.div 
            initial={{x:-10, opacity:0}}
            animate={{x:0 , opacity:1}}
            transition={{duration:0.25, }}
            className="bg-gradient-to-br flex items-center from-neutral-900/30 via-zinc-800/75 to-neutral-900/75 text-zinc-100 border border-zinc-700/60 rounded-xl shadow-2xl p-4  text-center font-medium tracking-wide">
			    <ChevronRight/>	{message}
			</motion.div>
	);
}
