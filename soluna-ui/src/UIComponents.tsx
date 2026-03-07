import { IconPlay } from './Icons';

export const TopMenuBar = ({
  menuOpen, setMenuOpen, handleAddFile, openFile, fileInputRef,
  handleFileRead, triggerAnalysis, activeFileContent, handleSaveFile
}: any) => (
  <div className="h-9 bg-zinc-950 flex items-center px-3 text-[13px] border-b border-zinc-900 z-50 shrink-0 rounded-none">
    <div className="flex items-center gap-2 mr-6 opacity-90">
      <img src="/src/assets/logo.png" alt="Logo" className="w-5 h-5 rounded-none" />
    </div>
    <div className="relative">
      <button
        className={`px-3 py-1 hover:bg-zinc-800 rounded-none transition-colors ${menuOpen === 'file' ? 'bg-zinc-800 text-yellow-500' : ''}`}
        onClick={() => setMenuOpen(menuOpen === 'file' ? null : 'file')}
      >
        File
      </button>
      {menuOpen === 'file' && (
        <div className="absolute top-full left-0 mt-1 w-48 bg-zinc-900 border border-zinc-800 shadow-2xl py-1 z-50 rounded-none">
          <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors rounded-none" onClick={handleAddFile}>New File</button>
          <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors rounded-none" onClick={openFile}>Open File...</button>
          <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors rounded-none" onClick={handleSaveFile}>Save File</button>
          <div className="h-px bg-zinc-800 my-1"></div>
          <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors rounded-none" onClick={() => window.location.reload()}>Exit</button>
        </div>
      )}
    </div>
    <div className="flex items-center gap-4 ml-6">
      <button
        onClick={() => triggerAnalysis(activeFileContent)}
        className="flex items-center gap-1.5 px-3 py-1 bg-yellow-500 text-black hover:bg-yellow-400 font-bold rounded-none text-[11px] uppercase tracking-wider transition-colors shadow-sm"
        title="Run Compiler Pipeline"
      >
        <IconPlay /> Run
      </button>
    </div>
    <input type="file" ref={fileInputRef} onChange={handleFileRead} className="hidden" />
    <div className="flex-1"></div>
    <div className="text-[11px] text-zinc-600 font-mono">SOLUNA DEV ENVIRONMENT</div>
  </div>
);

export const StatusBar = ({
  wsStatus, errorsLength, showLeftSidebar, setShowLeftSidebar,
  showTerminal, setShowTerminal, showRightSidebar, setShowRightSidebar, tokensLength
}: any) => (
  <div className="h-6 bg-yellow-500 flex items-center px-3 text-black text-[11px] font-bold select-none justify-between shrink-0 rounded-none">
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-1">
        <span className={`w-2 h-2 rounded-full ${wsStatus === 'CONNECTED' ? 'bg-black animate-pulse' : 'bg-red-600'}`}></span>
        {wsStatus}
      </div>
      {errorsLength > 0 && (
        <div className="flex items-center gap-1 px-2 py-0.5 bg-black/10 rounded-none cursor-pointer hover:bg-black/20" onClick={() => { setShowTerminal(true); }}>
          <span>!</span> {errorsLength} Error(s)
        </div>
      )}
    </div>
    <div className="flex items-center gap-4">
      <div className="flex gap-1 border-r border-black/10 pr-4 mr-1">
        <button onClick={() => setShowLeftSidebar(!showLeftSidebar)} className={`hover:bg-black/10 px-1 rounded-none ${!showLeftSidebar && 'opacity-50'}`}>[Sidebar]</button>
        <button onClick={() => setShowTerminal(!showTerminal)} className={`hover:bg-black/10 px-1 rounded-none ${!showTerminal && 'opacity-50'}`}>[Terminal]</button>
        <button onClick={() => setShowRightSidebar(!showRightSidebar)} className={`hover:bg-black/10 px-1 rounded-none ${!showRightSidebar && 'opacity-50'}`}>[Output]</button>
      </div>
      <span>Ln {tokensLength}</span>
      <span>Soluna 0.50</span>
    </div>
  </div>
);