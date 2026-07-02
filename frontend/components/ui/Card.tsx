import { type HTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card({ className, interactive = false, ...props }, ref) {
  return (
    <div
      ref={ref}
      className={cn(
        "rounded-md border border-line bg-surface transition-[transform,box-shadow,border-color] duration-200 ease-out",
        interactive &&
          "hover:-translate-y-0.5 hover:border-line-strong hover:shadow-[0_1px_2px_rgba(20,24,26,0.04),0_8px_24px_-10px_rgba(20,24,26,0.14)]",
        className,
      )}
      {...props}
    />
  );
});
