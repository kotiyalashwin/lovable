import { ChevronRight } from "lucide-react";
import * as motion from "motion/react-client"
export default function CreatedMessage({ message }: { message: string }) {
    
	return (
		
			<motion.div 
            initial={{x:-10, opacity:0}}
            animate={{x:0 , opacity:1}}
            transition={{duration:0.25, }}
            className=" flex items-center text-lg  p-2  text-center font-thin  tracking-tight text-neutral-400 italic">
			    <ChevronRight size={18}/>
            Created <span className="ml-2 border-2 text-white shadow-md shadow-purple-400 border-neutral-400 px-2 skew-2">{message}</span>
			</motion.div>
	);
}
