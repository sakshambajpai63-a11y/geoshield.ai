import { BrowserRouter, Routes, Route } from "react-router-dom";
import CitizenPortal from "./pages/CitizenPortal";
import OfficerConsole from "./pages/OfficerConsole";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CitizenPortal />} />
        <Route path="/officer" element={<OfficerConsole />} />
      </Routes>
    </BrowserRouter>
  );
}
