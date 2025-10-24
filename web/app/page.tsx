import type { Easing } from "motion";
import * as motion from "motion/react-client";
import InputCard from "@/components/prompt-card";

const containerVariants = {
	hidden: {},
	show: {
		transition: { staggerChildren: 0.9 },
	},
};

const childVariants = {
	hidden: { opacity: 0, y: 20 },
	show: {
		opacity: 1,
		y: 0,
		transition: { duration: 1.5, ease: "easeOut" as Easing },
	},
};

export default function Home() {
	return (
		<div className="h-screen w-screen flex justify-center items-center relative overflow-hidden bg-black">
			<motion.div
				variants={containerVariants}
				initial="hidden"
				animate="show"
				className="absolute flex justify-evenly inset-0 w-screen"
			>
				{["LOVABLE"].map((word) => (
					<motion.div
						key={`tex-${word}`}
						className="text-9xl text-neutral-400/30 font-light tracking-tight"
						variants={childVariants}
					>
						{word}
					</motion.div>
				))}
			</motion.div>

			<InputCard />
			<div className="absolute inset-0 w-screen flex items-end justify-center pointer-events-none">
				<div
					className="absolute h-[1200px] w-full translate-y-1/2 rounded-full blur-3xl
                    bg-[radial-gradient(circle_at_center,_#6D28D9_0%,_#3B82F6_40%,_transparent_80%)]"
				/>
				<motion.div
                    
					className="absolute h-[1000px] w-[1400px] translate-y-1/2 rounded-full blur-2xl
          bg-[radial-gradient(circle_at_center,_#A855F7_0%,_#6D28D9_50%,_transparent_100%)]"
				/>

				<motion.div
					className="absolute h-[800px] w-[1200px] translate-y-1/2 rounded-full blur-2xl opacity-70
          bg-[radial-gradient(circle_at_center,_#C084FC_0%,_#8B5CF6_40%,_transparent_100%)]"
				/>
			</div>
		</div>
	);
}
