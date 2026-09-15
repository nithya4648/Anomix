import { Link } from 'react-router-dom'

export const Footer = () => {
  return (
    <footer className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
      <Link to="/privacy" className="hover:text-slate-300">
        Privacy Policy
      </Link>
      <span className="mx-2 text-slate-700">|</span>
      <Link to="/terms" className="hover:text-slate-300">
        Terms & Conditions
      </Link>
    </footer>
  )
}
