"use client";

import LoginModal from "@/components/auth/LoginModal";
import { useState } from "react";

export default function Home() {
  // 로그인 모달 제어 state
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  return (
    <>
      <div className="flex flex-col items-center">
        <h1>너나들이 메인 화면입니다.</h1>
        <button
          className="btn text-[20px] h-[55px] mt-[24px] bg-[#f7d943] rounded-[8px] px-4"
          onClick={() => setIsLoginModalOpen(true)}
        >
          로그인 테스트하기
        </button>
        <LoginModal
          isOpen={isLoginModalOpen}
          onClick={() => setIsLoginModalOpen(false)}
        />
      </div>
    </>
  );
}
