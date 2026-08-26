"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { UserCircle, X, Save } from "lucide-react";

export function LearnerProfileWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);

  const [profileData, setProfileData] = useState({
    ageRole: "",
    goal: "",
    interests: "",
    tone: ""
  });

  useEffect(() => {
    setMounted(true);
    const savedData = localStorage.getItem("learnerProfile_v2_data");
    if (savedData) {
      try {
        const parsed = JSON.parse(savedData);
        setProfileData(parsed);
        setHasProfile(true);
      } catch (e) {}
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem("learnerProfile_v2_data", JSON.stringify(profileData));
    
    const compiledText = `
- 연령대 및 직업: ${profileData.ageRole || "일반적인 성인 학습자"}
- 학습 목표: ${profileData.goal || "내용의 정확한 이해와 숙지"}
- 주요 관심사: ${profileData.interests || "특별한 관심사 없음"}
- AI에게 원하는 어조: ${profileData.tone || "친절하고 전문적인 어조"}
    `.trim();
    
    localStorage.setItem("learnerProfile_v2", compiledText);
    setHasProfile(true);
    setIsOpen(false);
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="p-2 rounded-full hover:bg-muted transition-colors flex items-center gap-2 group relative text-muted-foreground hover:text-primary"
        title="나의 페르소나 설정"
      >
        <UserCircle size={22} className={hasProfile ? "text-primary" : ""} />
        {hasProfile && (
          <span className="absolute top-1 right-1 w-2 h-2 bg-green-500 rounded-full border-2 border-card"></span>
        )}
      </button>

      {isOpen && mounted && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <div className="bg-card border-2 border-border/50 rounded-3xl p-6 md:p-8 max-w-lg w-full shadow-2xl shadow-primary/10 relative overflow-y-auto max-h-[90vh] flex flex-col eink-border">
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground p-1 rounded-full hover:bg-muted transition-colors"
            >
              <X size={24} />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <span className="text-4xl drop-shadow-sm">🎓</span>
              <div>
                <h2 className="text-2xl font-extrabold tracking-tight">초개인화 맞춤 설정</h2>
                <p className="text-sm text-muted-foreground font-medium mt-1">
                  나만의 1:1 과외 선생님을 만들어보세요.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-muted-foreground mb-1 ml-1">
                  직업 및 연령대
                </label>
                <input
                  type="text"
                  value={profileData.ageRole}
                  onChange={(e) => setProfileData({...profileData, ageRole: e.target.value})}
                  placeholder="예: 중학교 2학년, 50대 은퇴자, 문과 대학생"
                  className="w-full bg-muted/50 border-none rounded-xl p-3 outline-none text-sm font-medium focus:ring-2 focus:ring-primary/50 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-muted-foreground mb-1 ml-1">
                  학습 목표
                </label>
                <input
                  type="text"
                  value={profileData.goal}
                  onChange={(e) => setProfileData({...profileData, goal: e.target.value})}
                  placeholder="예: 내일 학교 시험 대비, 가벼운 교양 쌓기, 실무 바로 적용"
                  className="w-full bg-muted/50 border-none rounded-xl p-3 outline-none text-sm font-medium focus:ring-2 focus:ring-primary/50 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-muted-foreground mb-1 ml-1 flex items-center justify-between">
                  <span>주요 관심사 (비유 생성용)</span>
                  <span className="text-xs text-primary bg-primary/10 px-2 py-0.5 rounded-full">중요!</span>
                </label>
                <input
                  type="text"
                  value={profileData.interests}
                  onChange={(e) => setProfileData({...profileData, interests: e.target.value})}
                  placeholder="예: 리그오브레전드, K-POP, 요리, 부동산, 축구"
                  className="w-full bg-muted/50 border-none rounded-xl p-3 outline-none text-sm font-medium focus:ring-2 focus:ring-primary/50 transition-all"
                />
                <p className="text-xs text-muted-foreground mt-2 ml-1">
                  💡 이 항목을 자세히 적을수록, 어려운 개념이 나올 때 <strong>관심사에 빗대어 찰떡같이 비유</strong>해 줍니다!
                </p>
              </div>

              <div>
                <label className="block text-sm font-bold text-muted-foreground mb-1 ml-1">
                  원하는 AI 어조
                </label>
                <input
                  type="text"
                  value={profileData.tone}
                  onChange={(e) => setProfileData({...profileData, tone: e.target.value})}
                  placeholder="예: 친절하고 다정한 선생님, 군대식 다나까, 인터넷 밈 듬뿍"
                  className="w-full bg-muted/50 border-none rounded-xl p-3 outline-none text-sm font-medium focus:ring-2 focus:ring-primary/50 transition-all"
                />
              </div>

              <div className="pt-2">
                <button
                  onClick={handleSave}
                  className="w-full bg-primary text-primary-foreground font-bold px-4 py-4 rounded-xl hover:opacity-90 active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  <Save size={18} />
                  저장하고 맞춤형 과외 시작하기
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
