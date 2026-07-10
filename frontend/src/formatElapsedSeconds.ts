export function formatElapsedSeconds(milliseconds: number): string {
  const seconds = milliseconds / 1000;
  const formattedSeconds =
    seconds < 1 ? seconds.toFixed(2) : seconds.toFixed(1).replace(/\.0$/, "");

  return `${formattedSeconds} ${formattedSeconds === "1" ? "second" : "seconds"}`;
}
