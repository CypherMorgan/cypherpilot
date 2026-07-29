/** Terminal-style animated logo component.

Renders ``>CypherPilot_`` with a blinking cursor, matching the
header animation style from cyphermorgan's portfolio.

Two variants:
- ``full`` — the complete ``> CypherPilot_`` line (default)
- ``compact`` — just the blinking ``CP_`` for collapsed sidebars
*/

interface AnimatedLogoProps {
  variant?: "full" | "compact";
  className?: string;
}

export function AnimatedLogo({ variant = "full", className = "" }: AnimatedLogoProps) {
  if (variant === "compact") {
    return (
      <span className={`inline-flex items-baseline font-mono text-lg font-bold tracking-tight ${className}`}>
        <span className="text-muted-foreground">CP</span>
        <span className="animate-cursor-blink text-primary">_</span>
        <style>{`@keyframes blink-logo { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } } .animate-cursor-blink { animation: blink-logo 1s step-end infinite; }`}</style>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-baseline font-mono text-lg font-bold tracking-tight ${className}`}>
      <span className="text-muted-foreground">&gt;</span>
      <span className="text-foreground">Cypher</span>
      <span className="text-primary">Pilot</span>
      <span className="animate-cursor-blink text-primary">_</span>
      <style>{`@keyframes blink-logo { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } } .animate-cursor-blink { animation: blink-logo 1s step-end infinite; }`}</style>
    </span>
  );
}
