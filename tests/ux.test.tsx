// @vitest-environment jsdom
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { Field, Notice, Button } from "../packages/ux/src/index";
afterEach(cleanup);
describe("shared UX contracts", () => {
  it("connects labels and help text to the input", () => {
    render(<Field id="email" label="Email" hint="Use your work email" />);
    expect(
      screen.getByRole("textbox", { name: "Email" }),
    ).toHaveAccessibleDescription("Use your work email");
  });
  it("announces errors", () => {
    render(<Notice error>Proposal expired</Notice>);
    expect(screen.getByRole("alert")).toHaveTextContent("Proposal expired");
  });
  it("prevents duplicate submissions while busy", async () => {
    const click = vi.fn();
    render(
      <Button disabled onClick={click}>
        Apply
      </Button>,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(click).not.toHaveBeenCalled();
  });
});
