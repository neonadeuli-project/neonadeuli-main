"use client";

import { useState } from "react";
import Image from "next/image";
import closeBtn from "@/assets/images/close_btn.png";
import googleLoginBtn from "@/assets/images/google_login.png";
import kakaoLoginBtn from "@/assets/images/kakao_login.png";
import naverLoginBtn from "@/assets/images/naver_login.png";

type LoginModalPropsType = {
  isOpen: boolean;
  onClick: () => void;
};

export default function LoginModal({ isOpen, onClick }: LoginModalPropsType) {
  const [isCloseAnimating, setIsCloseAnimating] = useState(false);

  // 닫기버튼 클릭 이벤트 핸들러
  const onClickCloseHandler = () => {
    // 닫기 애니메이션 시작
    setIsCloseAnimating(true);
    setTimeout(() => {
      // 3초 뒤, 모달창 상태 false
      onClick();
      // 3초 뒤, 애니메이션 false
      setIsCloseAnimating(false);
    }, 300);
  };

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="w-full h-full bg-black bg-opacity-60 flex items-center justify-center">
            <div
              className={`w-[375px] h-[376px] fixed bottom-0 bg-white rounded-t-[20px] p-[30px] transition-transform duration-300 ease-in-out ${
                isCloseAnimating ? "animate-slide-bottom" : "animate-slide-top"
              }`}
              style={{
                animation: isCloseAnimating
                  ? "slide-bottom 0.3s forwards"
                  : "slide-top 0.3s forwards",
              }}
            >
              <div className="flex justify-end" onClick={onClickCloseHandler}>
                <Image src={closeBtn} alt="close-button" width={20} />
              </div>
              <div className="flex flex-col justify-center items-center mt-[24px]">
                <p className="text-[20px] font-medium">3초만에 로그인하고</p>
                <p className="text-[20px] font-medium">
                  너나들이를 이용해보세요!
                </p>
                <button className="btn relative flex w-full items-center justify-center h-[55px] mt-[24px] bg-[#F5F5F5] rounded-[8px] px-4">
                  <span className="absolute left-4">
                    <Image
                      className="mr-3"
                      src={googleLoginBtn}
                      alt="google-login"
                      width={38}
                      height={38}
                    />
                  </span>
                  <span className="text-[16px] font-medium">구글 로그인</span>
                </button>
                <p className="pt-[24px] pb-[16px] text-[#808080] text-[14px] cursor-pointer">
                  다른 방법으로 로그인 하기
                </p>
                <div className="flex w-[130px] justify-between">
                  <button className="hover:bg-gray-200 rounded-[50%]">
                    <Image
                      src={kakaoLoginBtn}
                      alt="kakao-button"
                      width={50}
                      height={50}
                      className="btn"
                    />
                  </button>
                  <button className="hover:bg-gray-200 rounded-[50%]">
                    <Image
                      src={naverLoginBtn}
                      alt="naver-button"
                      width={50}
                      height={50}
                      className="btn"
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
