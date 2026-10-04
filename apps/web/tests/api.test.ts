import { describe, expect, it, vi } from "vitest";
import { api } from "../lib/api";

describe("API client", () => {
  it("posts interpretation requests without converting decimal strings", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ interpretation: { objective: "save" } }), { status: 200 }),
    );

    await api.interpret("Save ₹50,000");
    const body = JSON.parse(fetchMock.mock.calls[0][1]?.body as string);
    expect(body.decision).toBe("Save ₹50,000");
    fetchMock.mockRestore();
  });
});
