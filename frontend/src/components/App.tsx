"use client";

import { useState } from "react";
import Sidebar, { type ScreenId } from "./Sidebar";
import ConfirmModal from "./ConfirmModal";
import ChatScreen from "./chat/ChatScreen";
import TasksScreen from "./tasks/TasksScreen";
import RemindersScreen from "./reminders/RemindersScreen";
import BriefingScreen from "./briefing/BriefingScreen";
import NotesScreen from "./notes/NotesScreen";
import LogsScreen from "./logs/LogsScreen";
import SettingsScreen from "./settings/SettingsScreen";
import { useConfirm } from "@/hooks/useConfirm";

export default function App() {
  const [active, setActive] = useState<ScreenId>("chat");
  const confirm = useConfirm();

  return (
    <div className="app">
      <Sidebar active={active} onSelect={setActive} />
      <main className="main">
        {active === "chat"      && <ChatScreen confirm={confirm} />}
        {active === "tasks"     && <TasksScreen confirm={confirm} />}
        {active === "reminders" && <RemindersScreen confirm={confirm} />}
        {active === "briefing"  && <BriefingScreen />}
        {active === "notes"     && <NotesScreen />}
        {active === "log"       && <LogsScreen />}
        {active === "settings"  && <SettingsScreen confirm={confirm} />}
      </main>
      <ConfirmModal {...confirm.props} />
    </div>
  );
}
