import { Lightbulb } from "lucide-react";
import * as motion from "motion/react-client";
import { Card, CardContent, CardHeader } from "../ui/card";

const Thinking = ({ message }: { message: string }) => {
	return (
		<motion.div
			initial={{ scale: 0, opacity: 0, originX: 0, originY: 0 }}
			animate={{ scale: 1, opacity: 1 }}
			transition={{ duration: 0.5, ease: "easeOut" }}
		>
			<Card>
				<CardHeader className="flex items-center gap-2 text-neutral-400">
					<Lightbulb size={20} />
					Thought Process
				</CardHeader>
				<CardContent className="space-y-2 text-sm text-neutral-300">
					{message}
				</CardContent>
			</Card>
		</motion.div>
	);
};

export default Thinking;
