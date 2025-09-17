import React from 'react'

const App: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="p-8 bg-white rounded-xl shadow border w-full max-w-md">
        <h1 className="text-2xl font-bold text-blue-600">Vite + React + TS + Tailwind</h1>
        <p className="mt-3 text-gray-700">Tailwind v4 успешно подключён.</p>
        <button className="mt-6 rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Кнопка</button>
      </div>
    </div>
  )
}

export default App
