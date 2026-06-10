import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoadsMain } from './loads-main';

describe('LoadsMain', () => {
  let component: LoadsMain;
  let fixture: ComponentFixture<LoadsMain>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoadsMain],
    }).compileComponents();

    fixture = TestBed.createComponent(LoadsMain);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
