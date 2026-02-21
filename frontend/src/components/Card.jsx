import React from "react";

export default function Card({ children, selected, onClick }) {
  return (
    <div
      className={`option-card ${selected ? "selected" : ""}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
}