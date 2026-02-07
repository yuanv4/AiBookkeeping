export function applyUtcDateRangeFilter(
  where: Record<string, unknown>,
  startDate?: string,
  endDate?: string
): void {
  if (!startDate && !endDate) return;
  const occurredAt: Record<string, Date> = {};
  if (startDate) {
    occurredAt.gte = parseUtcDateStart(startDate);
  }
  if (endDate) {
    const end = parseUtcDateStart(endDate);
    end.setUTCDate(end.getUTCDate() + 1);
    occurredAt.lt = end;
  }
  where.occurredAt = occurredAt;
}

function parseUtcDateStart(value: string): Date {
  const [year, month, day] = value.split("-").map((part) => Number(part));
  return new Date(Date.UTC(year, month - 1, day));
}
