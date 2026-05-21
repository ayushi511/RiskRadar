export default function App() {
  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      <iframe
        src="/map.html"
        title="Disaster Map"
        width="100%"
        height="100%"
        style={{
          border: "none",
        }}
      />
    </div>
  );
}