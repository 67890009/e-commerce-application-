// src/app/(auth)/layout.js

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      {children}
    </div>
  );
}