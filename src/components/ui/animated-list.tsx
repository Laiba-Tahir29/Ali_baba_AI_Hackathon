import React from "react";
import { motion, useReducedMotion, type Variants } from "framer-motion";
import { cn } from "../../lib/utils";

export interface AnimatedListProps {
  /** List children or elements to be staggered */
  children: React.ReactNode;
  /** Container CSS classes (e.g. grid or flex layout) */
  className?: string;
  /** Fast stagger delay per item in seconds (40-60ms = 0.04 - 0.06s) */
  staggerDelay?: number;
  /** Initial delay before stagger starts */
  delay?: number;
  /** Animation duration per child (kept under 250ms) */
  duration?: number;
  /** Y displacement in pixels */
  yOffset?: number;
  /** Whether to animate as a grid layout or direct container */
  as?: keyof React.JSX.IntrinsicElements;
}

export const AnimatedList: React.FC<AnimatedListProps> = ({
  children,
  className,
  staggerDelay = 0.05, // 50ms stagger
  delay = 0,
  duration = 0.22, // 220ms duration (well under 300ms guardrail)
  yOffset = 8,
}) => {
  const shouldReduceMotion = useReducedMotion();

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : staggerDelay,
        delayChildren: delay,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: shouldReduceMotion
      ? { opacity: 0 }
      : { opacity: 0, y: yOffset },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration,
        ease: [0.25, 0.1, 0.25, 1], // clean easeOut
      },
    },
  };

  const childArray = React.Children.toArray(children);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className={cn(className)}
    >
      {childArray.map((child, index) => {
        if (!React.isValidElement(child)) return child;

        return (
          <motion.div
            key={child.key ?? index}
            variants={itemVariants}
            className="w-full h-full"
          >
            {child}
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default AnimatedList;
