// app/InputCard.tsx
"use client";

import { useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { SendHorizonal } from "lucide-react";
import * as motion from "motion/react-client";
import { generateRandomString } from "@/lib/randomId";

export default function InputCard() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    const value = inputRef.current?.value;
    if (value) {
      localStorage.setItem("prompt", value);
      const randomId = generateRandomString(10)  
      router.push(`/project/${randomId}`);
    }
  };

  return (
    <div className="w-full z-10 max-w-7xl flex justify-center">
      <Card className="max-w-3xl w-full bg-neutral-900 border-neutral-700">
        <CardContent>
          <input
            ref={inputRef}
            name="prompt"
            placeholder="Describe your next masterpiece..."
            className="block p-4 focus:outline-none w-full border-none text-xl  bg-neutral-900 text-neutral-200 placeholder:text-neutral-500"
          />
          <Button onClick={handleSubmit} className="tracking-widest mt-4">
            SUBMIT{" "}
            <motion.span whileHover={{ x: 12, opacity: 0 }}>
              <SendHorizonal />
            </motion.span>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

