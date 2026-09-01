import './AppShell.css'
import DesktopSidebar from './DesktopSidebar'
import MobileNav from './MobileNav'

export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <DesktopSidebar />
      <main className="app-shell__main">
        {children}
      </main>
      <MobileNav />
    </div>
  )
}
